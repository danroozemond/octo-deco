# Please see LICENSE.md
import BuhlmannConstants
import Gas
import Util


class AmbientToGF:
    """
    Helper class to store/keep gradient factor line

    At first stop, allowed supersaturation is GF_LOW % (eg. 35%)
    At surfacing, allowed supersaturation is GF_HIGH % (eg. 70%)

    So, at p_first_stop, allowed supersat is gf_low
    and at p_surface, allowed supersat is gf_high
    We return a function that linearly interpolates; is flat outside the bounds
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

    def __init__(self, gf_low, gf_high, descent_speed, ascent_speed):
        self._constants = BuhlmannConstants.ZHL_16C_1a;
        self._n_tissues = self._constants.N_TISSUES;
        self.gf_low = gf_low;
        self.gf_high = gf_high;
        self.max_pO2_deco = 1.60;
        self._p_last_stop = 1.3;
        self._p_water_vapour = 0.0627;
        self.descent_speed = descent_speed;
        self.ascent_speed = ascent_speed;

    def description(self):
        return 'ZHL-16C GF %s/%s' % (self.gf_low, self.gf_high);

    """
    TissueState is represented as a list of current tissue loadings (N2, He)

    Note: Inspired gas loading equations depend on the partial pressure of inert gas in the alveolar.
    WV_Buhlmann = PP_H2O = 0.0627 bar
    """

    def cleared_tissue_state(self):
        gas = Gas.Air();
        return [ ((1.0 - self._p_water_vapour) * gas[ 'fN2' ], (1.0 - self._p_water_vapour) * gas[ 'fHe' ]) for i in
                 range(self._n_tissues) ];

    @staticmethod
    def _updated_partial_pressure(pp_tissue, pp_alveolar, halftime, duration):
        return pp_tissue + (1 - pow(.5, duration / halftime)) * (pp_alveolar - pp_tissue);

    def updated_tissue_state(self, state, duration, p_amb, gas):
        pp_amb_n2 = (p_amb - self._p_water_vapour) * gas[ 'fN2' ];
        pp_amb_he = (p_amb - self._p_water_vapour) * gas[ 'fHe' ];
        new_state = [
            (
            Buhlmann._updated_partial_pressure(state[ i ][ 0 ], pp_amb_n2, self._constants.N2_HALFTIMES[ i ], duration),
            Buhlmann._updated_partial_pressure(state[ i ][ 1 ], pp_amb_he, self._constants.HE_HALFTIMES[ i ], duration),
            ) for i in range(self._n_tissues) ];
        return new_state;

    """
    Decompression (status, stops) information

    From Deco for Divers, Mark Powell, page 179:
    P_{amb tol} = (P_comp - a) * b
    where 
    P_{amb tol} is pressure you could drop to,
    P_comp is inert gas pressure in the compartment
    a,b are the usual Buhlmann params

    For Trimix, Pcomp = P_N2 + P_He
    You must decide which a/b to use. If you just use N2 you get a more conservative schedule; 
    alternatively lineartly interpolate the a and b values themselves, 
    based on proportions of gas load in each tissue
    """

    def _get_coeffs_a_b(self, i, tissue_state_i):
        a = self._constants.N2_A_VALUES[ i ];
        b = self._constants.N2_B_VALUES[ i ];
        pp_n2, pp_he = tissue_state_i;
        if pp_he > 0.0:
            # Trimix case
            a_he = self._constants.HE_A_VALUES[ i ];
            b_he = self._constants.HE_B_VALUES[ i ];
            a = pp_n2 / (pp_n2 + pp_he) * a + pp_he / (pp_n2 + pp_he) * a_he;
            b = pp_n2 / (pp_n2 + pp_he) * b + pp_he / (pp_n2 + pp_he) * b_he;
        return a, b;

    def _workmann_m0(self, p_amb, i, tissue_state_i):
        a, b = self._get_coeffs_a_b(i, tissue_state_i);
        m0 = a + p_amb / b;
        return m0;

    def _p_ceiling_for_gf_now(self, tissue_state, gf_now):
        # Derived from _GF99_new as defined below
        gff = gf_now / 100.0;

        # Returns the ceiling for one particular tissue
        def for_one(i):
            a, b = self._get_coeffs_a_b(i, tissue_state[ i ]);
            p_amb = (sum(tissue_state[ i ]) - a * gff) / (gff / b - gff + 1);
            return p_amb;

        p_ceilings = [ for_one(i) for i in range(self._n_tissues) ];
        return max(p_ceilings);

    def p_ceiling_for_gf(self, tissue_state, amb_to_gf):
        pc = self._p_ceiling_for_gf_now(tissue_state, amb_to_gf.gf_high);
        return pc;

    def _GF99_new(self, tissue_state, p_amb):
        def for_one(i):
            m0 = self._workmann_m0(p_amb, i, tissue_state[ i ]);
            return 100.0 * (sum(tissue_state[ i ]) - p_amb) / (m0 - p_amb);

        return [ max(0.0, for_one(i)) for i in range(self._n_tissues) ];

    def _best_deco_gas(self, p_amb, gases):
        # What is the best deco gas at this ambient pressure?
        suitable = [ gas for gas in gases if p_amb * gas[ 'fO2' ] <= self.max_pO2_deco ];
        assert (len(suitable) > 0);
        gas = max(gases, key = lambda g: g[ 'fO2' ]);
        return gas;

    def _time_to_stay_at_stop(self, p_amb, tissue_state, gas, amb_to_gf):
        # Returns both the time (integer) and the updated tissue_state.
        # Straight computation is possible (even for Trimix), but comes down to solving
        # a pretty messy quadratic equation, and I'm too lazy for that.
        # Binary search is fast enough and more robust (and again, lazy)
        p_amb_next_stop = Util.next_stop_Pamb(p_amb);
        gf99allowed_next = amb_to_gf(p_amb_next_stop);

        def max_over_supersat(t):
            ts2 = self.updated_tissue_state(tissue_state, t, p_amb, gas);
            gf99attained_next = self._GF99_new(ts2, p_amb_next_stop);
            x = [ p - gf99allowed_next for p in gf99attained_next ];
            return max(x);

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
        tissue_state_after_stop = self.updated_tissue_state(tissue_state, stop_length, p_amb, gas);
        return stop_length, tissue_state_after_stop;

    def _get_ambtogf(self, tissue_state, p_amb, p_target, amb_to_gf = None):
        # Allowed to pass in amb_to_gf in case we recompute part of the deco after it has already started
        # Determine ceiling, and allowed supersaturation at the various levels
        if amb_to_gf is None:
            p_ceiling = self._p_ceiling_for_gf_now(tissue_state, self.gf_low);
            p_first_stop = Util.Pamb_to_Pamb_stop(p_ceiling);  # First stop is rounded (to 3m)
            amb_to_gf = AmbientToGF(p_first_stop, p_target, self.gf_low, self.gf_high);
            return amb_to_gf;
        else:
            p_ceiling = self.p_ceiling_for_gf(tissue_state, amb_to_gf);
            # The original amb_to_gf should be considered void if the ceiling is now more than orig first stop
            if p_ceiling > amb_to_gf.p_first_stop:
                return self._get_ambtogf(tissue_state, p_amb, p_target);
            return amb_to_gf;

    def compute_deco_profile(self, tissue_state, p_amb, gases, p_target = 1.0, amb_to_gf = None):
        # Returns triples depth, length, gas
        amb_to_gf = self._get_ambtogf(tissue_state, p_amb, p_target, amb_to_gf);
        p_ceiling = self.p_ceiling_for_gf(tissue_state, amb_to_gf);
        assert p_ceiling < 100.0;  # Otherwise something very weird is happening
        p_first_stop = Util.Pamb_to_Pamb_stop(p_ceiling);  # First stop is rounded (to 3m)
        # 'Walk' up
        result = [ ];
        p_now = p_first_stop;
        while p_now > p_target + 0.01:
            gas = self._best_deco_gas(p_now, gases);
            stoplength, tissue_state = self._time_to_stay_at_stop(p_now, tissue_state, gas, amb_to_gf);
            result.append((Util.Pamb_to_depth(p_now), stoplength, gas));
            p_now = Util.next_stop_Pamb(p_now);
        return result, p_ceiling, amb_to_gf;

    def deco_info(self, tissue_state, depth, gases, amb_to_gf = None):
        p_amb = Util.depth_to_Pamb(depth);
        p_ceiling_99 = self._p_ceiling_for_gf_now(tissue_state, 99.0);
        # GF99: how do compartment pressure, ambient pressure, tolerance compare
        # the % makes most sense if ambient pressure is between compartment pressure and tolerance
        # if ambient pressure is bigger than compartment pressure: ongassing
        gf99s = self._GF99_new(tissue_state, p_amb);
        gf99 = max(gf99s);
        leading_tissue_i = gf99s.index(gf99);
        surfacegfs = self._GF99_new(tissue_state, 1.0);
        result = {'Ceil99': Util.Pamb_to_depth(p_ceiling_99),
                  'GF99': round(gf99, 1),
                  'SurfaceGF': round(max(surfacegfs), 1),
                  'SurfaceGFs': surfacegfs,
                  'LeadingTissueIndex': leading_tissue_i,
                  'allGF99s': gf99s
                  };

        # Below is about computing the decompression profile
        stops, p_ceiling, amb_to_gf = self.compute_deco_profile(tissue_state, p_amb, gases, amb_to_gf = amb_to_gf);
        result[ 'Ceil' ] = Util.Pamb_to_depth(p_ceiling);
        result[ 'Stops' ] = stops;
        nontrivialstops = [ s for s in stops if round(s[ 1 ]) >= 1 ];
        result[ 'FirstStop' ] = nontrivialstops[ 0 ][ 0 ] if len(nontrivialstops) > 0 else 0;
        result[ 'amb_to_gf' ] = amb_to_gf;
        result[ 'GFLimitNow' ] = amb_to_gf(p_amb) if amb_to_gf is not None else 0.0;
        result[ 'TTS' ] = depth / self.ascent_speed + sum([ s[ 1 ] for s in stops ]);

        # Done
        return result;

