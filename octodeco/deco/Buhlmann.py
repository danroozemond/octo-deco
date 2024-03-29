# Please see LICENSE.md
from . import BuhlmannConstants;
from . import Gas;
from . import TissueStateCython;
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
        self.p_surface = Util.SURFACE_PRESSURE;
        self.p_first_stop = max( p_first_stop, self.p_surface );
        self.gf_low = gf_low;
        self.gf_high = gf_high;
        self.p_target = p_target;


class Buhlmann:
    """
    Buhlmann class contains all essential logic for deco model
    """
    def __init__(self,
                 gf_low, gf_high,
                 descent_speed, ascent_speed,
                 max_pO2_deco, gas_swich_mins,
                 last_stop_depth):
        self._constants = BuhlmannConstants.ZHL_16C_1a;
        self._rq = 0.9; # Respiratory Quotient.
        self._n_tissues = self._constants.N_TISSUES;
        self.TissueState = TissueStateCython.TissueState;
        self.gf_low = gf_low;
        self.gf_high = gf_high;
        self.max_pO2_deco = max_pO2_deco;
        self.descent_speed = descent_speed;
        self.ascent_speed = ascent_speed;
        self.gas_switch_mins = gas_swich_mins;
        self.last_stop_depth = last_stop_depth;
        self.stop_length_precision = 0.08;
        # After 8 halftimes, residual is less than 0.5%, so that's infinite enough.
        self._stop_length_infinity = 8*self._constants.N2_HALFTIMES[-1];

    def description(self):
        return 'ZHL-16C GF %s/%s' % (self.gf_low, self.gf_high);

    def set_gf(self, gf_low, gf_high):
        self.gf_low = gf_low;
        self.gf_high = gf_high;

    def cleared_tissue_state(self):
        return self.TissueState(self._constants, self._rq);

    #
    # NDL, deco stop, deco profile computations
    #
    def NDL(self, tissue_state, amb_to_gf, p_amb, gas):
        # Binary search, t0/h/t1 the time we still stay at this depth
        #   t0 < h < t1
        #   max_over_supersat(t0) < 0
        #   max_over_supersat(t1) > 0

        def max_over_supersat(t):
            ts2 = tissue_state.updated_state(t, p_amb, gas);
            ts3 = self._update_tissue_state_travel(ts2, p_amb, Util.SURFACE_PRESSURE, gas);
            return ts3.max_over_supersat(amb_to_gf, Util.SURFACE_PRESSURE);

        t0 = 0.0;
        t1 = self._stop_length_infinity;
        if max_over_supersat(t0) > 0:
            # Already in deco
            return t0;
        if max_over_supersat(t1) < 0:
            # We can stay here indefinitely
            return t1;

        while t1 - t0 > 0.01:
            h = t0 + (t1-t0)/2;
            if max_over_supersat(h) < 0:
                t0 = h;
            else:
                t1 = h;

        return t0;

    def _best_deco_gas(self, p_amb, gases):
        return Gas.best_gas( gases, p_amb, self.max_pO2_deco );

    def _gas_switch_p_amb(self, gas):
        p_amb = self.max_pO2_deco / gas['fO2'];
        p_amb = Util.Pamb_to_Pamb_stop(p_amb, direction='up', last_stop_depth = self.last_stop_depth);
        return p_amb;

    def _time_to_stay_at_stop(self, p_amb, p_amb_next_stop, tissue_state, gas, amb_to_gf):
        # Returns both the time (integer) and the updated tissue_state.
        # Straight computation is possible (even for Trimix), but comes down to solving
        # a pretty messy quadratic equation, and I'm too lazy for that.
        # Binary search is fast enough and more robust (and again, lazy)
        def max_over_supersat(t):
            ts2 = tissue_state.updated_state(t, p_amb, gas);
            return ts2.max_over_supersat(amb_to_gf, p_amb_next_stop);

        # Binary search:
        #   t0 <= t <= t1, max_over_supersat(t) = 0.
        #   max_over_supersat(t0) > 0
        #   max_over_supersat(t1) < 0
        t0 = 0.0;
        t1 = 5.0;
        if max_over_supersat(t0) < 0:
            # Already OK
            return 0.0;
        #for t1, infinity is too long: staying at this stop depth forever may lead to
        #  too high loading for next stop (in the slow tissues). So there is a certain
        #  point in time where the faster tissues are fine (because of the stop) and
        #  the slower are still fine.
        while max_over_supersat(t1) > 0 and t1 < self._stop_length_infinity:
            t1 *= 2.0;
        if max_over_supersat(t1) > 0:
            # Still on-gassing
            return 0.0;
        while t1 - t0 > self.stop_length_precision:
            h = t0 + (t1 - t0) / 2;
            mosh = max_over_supersat(h);
            if mosh > 0:
                t0 = h;
            else:
                t1 = h;
        stop_length = t1;
        return stop_length;

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
            time = (p_amb - p_new_amb) / (self.ascent_speed * Util.BAR_PER_METER);
        elif p_amb < p_new_amb:
            time = (p_new_amb - p_amb) / (self.descent_speed * Util.BAR_PER_METER);
        if time == 0.0:
            return state;
        else:
            assert time > 0.0;
            p_avg = (p_amb + p_new_amb)/2.0;
            return state.updated_state(time, p_avg, gas);

    def _deco_profile_p_amb_next_stop(self, p_now, p_first_stop, current_gas, gases, add_gas_switch_time = True):
        # returns p_amb for next stop, p_amb for gas switch, gas to use at next stop
        if p_now > p_first_stop:
            p_amb_next_stop = p_first_stop;
        else:
            p_amb_next_stop = Util.next_stop_Pamb(p_now, last_stop_depth = self.last_stop_depth);
        # Do we need a gas switch?
        new_gas = self._best_deco_gas(p_amb_next_stop, gases);
        if new_gas != current_gas and p_first_stop > Util.SURFACE_PRESSURE and add_gas_switch_time:
            p_amb_gas_switch = self._gas_switch_p_amb(new_gas);
            if p_amb_next_stop-0.01 < p_amb_gas_switch < p_now-0.01:
                p_amb_next_stop = p_amb_gas_switch;
        return p_amb_next_stop, new_gas;

    def compute_deco_profile(self, tissue_state, p_amb, current_gas, gases,
                             p_target = Util.SURFACE_PRESSURE,
                             add_gas_switch_time = False, amb_to_gf = None):
        # Returns triples depth, length, gas
        amb_to_gf = self._get_ambtogf(tissue_state, p_amb, p_target, amb_to_gf);
        p_ceiling = tissue_state.p_ceiling_for_amb_to_gf(amb_to_gf);
        assert p_ceiling < 100.0;  # Otherwise something very weird is happening
        p_first_stop = Util.Pamb_to_Pamb_stop(p_ceiling, last_stop_depth = self.last_stop_depth);
        # Start at deepest point from first_stop at ambient
        p_now = max(p_first_stop, p_amb);
        # If we don't need to add gas_switch_time, instantly switch to the best gas
        if add_gas_switch_time:
            gas_now = current_gas;
        else:
            gas_now = self._best_deco_gas(p_now, gases);
        # 'walk up'
        result = [ ];
        while p_now > p_target + 0.01:
            p_amb_next_stop, gas_next_stop = self._deco_profile_p_amb_next_stop(p_now, p_first_stop, gas_now, gases,
                                                                                add_gas_switch_time = add_gas_switch_time);
            stoplength = self._time_to_stay_at_stop(p_now, p_amb_next_stop, tissue_state, gas_now, amb_to_gf);
            tissue_state = tissue_state.updated_state(stoplength, p_now, gas_now);
            if stoplength > self.stop_length_precision:
                result.append((Util.Pamb_to_depth(p_now), stoplength, gas_now));
            # Travel to next stop
            tissue_state = self._update_tissue_state_travel(tissue_state, p_now, p_amb_next_stop, gas_now);
            # Consider adding gas switch
            if gas_now != gas_next_stop and add_gas_switch_time:
                result.append((Util.Pamb_to_depth(p_amb_next_stop), self.gas_switch_mins, gas_now));
                tissue_state = tissue_state.updated_state( self.gas_switch_mins, p_amb_next_stop, gas_now );
                result.append((Util.Pamb_to_depth(p_amb_next_stop), 0.0, gas_next_stop));
            # Onto the next stop!
            p_now = p_amb_next_stop; gas_now = gas_next_stop;
        return result, p_ceiling, amb_to_gf;

    def deco_info(self, tissue_state, depth, gas, gases_carried, amb_to_gf = None):
        p_amb = Util.depth_to_Pamb(depth);
        p_ceiling_99 = tissue_state.p_ceiling_for_gf_now(99.0);
        # GF99: how do compartment pressure, ambient pressure, tolerance compare
        # the % makes most sense if ambient pressure is between compartment pressure and tolerance
        # if ambient pressure is bigger than compartment pressure: ongassing
        gf99s, gf99, leading_tissue_i = tissue_state.GF99_all_info(p_amb);
        surfacegf = tissue_state.GF99(Util.SURFACE_PRESSURE);
        result = {'Ceil99': Util.Pamb_to_depth(p_ceiling_99),
                  'GF99': round(gf99, 1),
                  'SurfaceGF': round(surfacegf, 1),
                  'LeadingTissueIndex': leading_tissue_i,
                  'allGF99s': gf99s
                  };

        # Below is about computing the decompression profile
        stops, p_ceiling, amb_to_gf = self.compute_deco_profile(tissue_state, p_amb, gas, gases_carried,
                                                                amb_to_gf = amb_to_gf);
        result[ 'Ceil' ] = Util.Pamb_to_depth(p_ceiling);
        result[ 'Stops' ] = stops;
        nontrivialstops = [ s for s in stops if s[ 1 ] >= .1 ];
        result[ 'FirstStop' ] = nontrivialstops[ 0 ][ 0 ] if len(nontrivialstops) > 0 else 0;
        result[ 'amb_to_gf' ] = amb_to_gf;
        result[ 'TTS' ] = depth / self.ascent_speed + sum([ s[ 1 ] for s in stops ]);
        result[ 'NDL' ] = self.NDL( tissue_state, amb_to_gf, p_amb, gas );

        # Done
        return result;
