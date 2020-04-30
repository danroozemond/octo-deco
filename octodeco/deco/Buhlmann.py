# Please see LICENSE.md
from . import BuhlmannConstants;
from . import TissueStateCython, TissueStateVerify;
from . import Util;


class AmbientToGF:
    """
    Helper class to store/keep gradient factor line

    At first stop, allowed supersaturation is GF_LOW % (eg. 35%)
    At surfacing, allowed supersaturation is GF_HIGH % (eg. 70%)

    So, at p_first_stop, allowed supersat is gf_low
    and at p_surface, allowed supersat is gf_high
    We return a function that linearly interpolates; is flat outside the bounds

    Actually, for smoothness, we use p_ceiling instead of p_first_stop.
    """

    def __init__(self, p_first_stop, p_target, gf_low, gf_high):
        self.p_first_stop = p_first_stop;
        self.p_surface = 1.0;
        self.gf_low = gf_low;
        self.gf_high = gf_high;
        self.p_target = p_target;

    def __call__(self, p_amb):
        if p_amb > self.p_first_stop:
            return self.gf_low;
        elif p_amb < self.p_surface:
            return self.gf_high;
        elif self.p_first_stop == self.p_surface:
            return self.gf_high;
        else:
            return self.gf_high + \
                   (p_amb - self.p_surface) / (self.p_first_stop - self.p_surface) * (self.gf_low - self.gf_high);


class Buhlmann:
    """
    Buhlmann class contains all essential logic for deco model
    """
    def __init__(self,
                 gf_low, gf_high,
                 descent_speed, ascent_speed,
                 debugTissueState = False):
        self._constants = BuhlmannConstants.ZHL_16C_1a;
        self._n_tissues = self._constants.N_TISSUES;
        self.TissueState = TissueStateCython.TissueState if not debugTissueState \
                    else   TissueStateVerify.TissueState;
        self.gf_low = gf_low;
        self.gf_high = gf_high;
        self.max_pO2_deco = 1.60;
        self._p_last_stop = 1.3;
        self.descent_speed = descent_speed;
        self.ascent_speed = ascent_speed;

    def description(self):
        return 'ZHL-16C GF %s/%s' % (self.gf_low, self.gf_high);

    def set_gf(self, gf_low, gf_high):
        self.gf_low = gf_low;
        self.gf_high = gf_high;

    def cleared_tissue_state(self):
        return self.TissueState(self._constants);

    #
    # NDL, deco stop, deco profile computations
    #
    def NDL(self, tissue_state, p_amb, gas):
        # Binary search, t0/h/t1 the time we still stay at this depth
        #   t0 < h < t1
        #   max_over_supersat(t0) < 0
        #   max_over_supersat(t1) > 0

        def max_over_supersat(t):
            ts2 = tissue_state.updated_state(t, p_amb, gas);
            ts3 = self._update_tissue_state_travel(ts2, p_amb, 1.0, gas);
            return ts3.GF99(1.0) - self.gf_high;

        t0 = 0.0;
        t1 = 1440.0;
        if max_over_supersat(t0) > 0:
            # Already in deco
            return t0;
        if max_over_supersat(t1) < 0:
            # We can stay here indefinitely
            return t1;

        while t1 - t0 > 0.01:
            h = t0 + (t1-t0)/2;
            # print('%.1f < %.1f < %.1f -> %.1f' %( t0,h,t1,max_over_supersat(h)));
            if max_over_supersat(h) < 0:
                t0 = h;
            else:
                t1 = h;

        return t0;

    def _best_deco_gas(self, p_amb, gases):
        # What is the best deco gas at this ambient pressure?
        suitable = [ gas for gas in gases if p_amb * gas[ 'fO2' ] <= self.max_pO2_deco ];
        assert (len(suitable) > 0);
        gas = max(suitable, key = lambda g: ( g[ 'fO2' ], -g['fHe'] ) );
        return gas;

    def _time_to_stay_at_stop(self, p_amb, p_amb_next_stop, tissue_state, gas, amb_to_gf):
        # Returns both the time (integer) and the updated tissue_state.
        # Straight computation is possible (even for Trimix), but comes down to solving
        # a pretty messy quadratic equation, and I'm too lazy for that.
        # Binary search is fast enough and more robust (and again, lazy)
        gf99allowed_next = amb_to_gf(p_amb_next_stop);

        def max_over_supersat(t):
            ts2 = tissue_state.updated_state(t, p_amb, gas);
            return ts2.GF99(p_amb_next_stop) - gf99allowed_next;

        # Binary search:
        #   t0 <= t <= t1, max_over_supersat(t) = 0.
        #   max_over_supersat(t0) > 0
        #   max_over_supersat(t1) < 0
        t0 = 0.0;
        t1 = 1440.0;
        if max_over_supersat(t0) < 0:
            return 0.0, tissue_state;
        assert max_over_supersat(t1) < 0;  # Otherwise even a 24hr stop is not enough??
        while t1 - t0 > 0.1:
            h = t0 + (t1 - t0) / 2;
            if max_over_supersat(h) > 0:
                t0 = h;
            else:
                t1 = h;
        stop_length = t1;
        tissue_state_after_stop = tissue_state.updated_state( stop_length, p_amb, gas );
        return stop_length, tissue_state_after_stop;

    def _get_ambtogf(self, tissue_state, p_amb, p_target, amb_to_gf = None):
        # Allowed to pass in amb_to_gf in case we recompute part of the deco after it has already started
        # Determine ceiling, and allowed supersaturation at the various levels
        if amb_to_gf is None:
            p_ceiling = tissue_state.p_ceiling_for_gf_now(self.gf_low);
            amb_to_gf = AmbientToGF(p_ceiling, p_target, self.gf_low, self.gf_high);
            return amb_to_gf;
        else:
            p_ceiling = tissue_state.p_ceiling_for_amb_to_gf(amb_to_gf);
            # The original amb_to_gf should be considered void if the ceiling is now more than orig first stop
            if p_ceiling > amb_to_gf.p_first_stop:
                return self._get_ambtogf(tissue_state, p_amb, p_target);
            return amb_to_gf;

    def _update_tissue_state_travel(self, state, p_amb, p_new_amb, gas):
        time = 0.0;
        if p_amb > p_new_amb:
            time = (p_amb - p_new_amb) / (self.ascent_speed/10);
        elif p_amb < p_new_amb:
            time = (p_new_amb - p_amb) / (self.descent_speed/10);
        if time == 0.0:
            return state;
        else:
            assert time > 0.0;
            p_avg = (p_amb + p_new_amb)/2.0;
            return state.updated_state(time, p_avg, gas);

    def compute_deco_profile(self, tissue_state, p_amb, gases, p_target = 1.0, amb_to_gf = None):
        # Returns triples depth, length, gas
        amb_to_gf = self._get_ambtogf(tissue_state, p_amb, p_target, amb_to_gf);
        p_ceiling = tissue_state.p_ceiling_for_amb_to_gf(amb_to_gf);
        assert p_ceiling < 100.0;  # Otherwise something very weird is happening
        p_first_stop = Util.Pamb_to_Pamb_stop(p_ceiling);  # First stop is rounded (to 3m)
        # Travel to first stop
        gas = self._best_deco_gas(p_amb, gases);
        tissue_state = self._update_tissue_state_travel(tissue_state, p_amb, p_first_stop, gas);
        # 'Walk' up
        result = [ ];
        p_now = p_first_stop;
        # Compute stops
        while p_now > p_target + 0.01:
            gas = self._best_deco_gas(p_now, gases);
            p_amb_next_stop = Util.next_stop_Pamb(p_now);
            stoplength, tissue_state = self._time_to_stay_at_stop(p_now, p_amb_next_stop, tissue_state, gas, amb_to_gf);
            result.append((Util.Pamb_to_depth(p_now), stoplength, gas));
            tissue_state = self._update_tissue_state_travel(tissue_state, p_now, p_amb_next_stop, gas);
            p_now = p_amb_next_stop;
        return result, p_ceiling, amb_to_gf;

    def deco_info(self, tissue_state, depth, gas, gases_carried, amb_to_gf = None):
        p_amb = Util.depth_to_Pamb(depth);
        p_ceiling_99 = tissue_state.p_ceiling_for_gf_now(99.0);
        # GF99: how do compartment pressure, ambient pressure, tolerance compare
        # the % makes most sense if ambient pressure is between compartment pressure and tolerance
        # if ambient pressure is bigger than compartment pressure: ongassing
        gf99s, gf99, leading_tissue_i = tissue_state.GF99_all_info(p_amb);
        surfacegf = tissue_state.GF99(1.0);
        result = {'Ceil99': Util.Pamb_to_depth(p_ceiling_99),
                  'GF99': round(gf99, 1),
                  'SurfaceGF': round(surfacegf, 1),
                  'LeadingTissueIndex': leading_tissue_i,
                  'allGF99s': gf99s
                  };

        # Below is about computing the decompression profile
        stops, p_ceiling, amb_to_gf = self.compute_deco_profile(tissue_state, p_amb, gases_carried,
                                                                amb_to_gf = amb_to_gf);
        result[ 'Ceil' ] = Util.Pamb_to_depth(p_ceiling);
        result[ 'Stops' ] = stops;
        nontrivialstops = [ s for s in stops if s[ 1 ] >= .1 ];
        result[ 'FirstStop' ] = nontrivialstops[ 0 ][ 0 ] if len(nontrivialstops) > 0 else 0;
        result[ 'amb_to_gf' ] = amb_to_gf;
        result[ 'GFLimitNow' ] = amb_to_gf(p_amb) if amb_to_gf is not None else 0.0;
        result[ 'TTS' ] = depth / self.ascent_speed + sum([ s[ 1 ] for s in stops ]);
        result[ 'NDL' ] = self.NDL( tissue_state, p_amb, gas );

        # Done
        return result;
