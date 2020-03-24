import BuhlmannConstants
import Gas
import Util

"""
Buhlmann class contains all essential logic for deco model
"""


class Buhlmann:
    def __init__(self, gf_low, gf_high):
        self._n_tissues = BuhlmannConstants.ZHL_16C_N_TISSUES;
        self._halftimes = {'N2': BuhlmannConstants.ZHL_16C_N2_HALFTIMES,
                           'He': BuhlmannConstants.ZHL_16C_HE_HALFTIMES};
        self._coeffs = {'N2': {'a': BuhlmannConstants.ZHL_16C_N2_A_VALUES,
                               'b': BuhlmannConstants.ZHL_16C_N2_B_VALUES},
                        'He': {'a': BuhlmannConstants.ZHL_16C_HE_A_VALUES,
                               'b': BuhlmannConstants.ZHL_16C_HE_B_VALUES}
                        };
        self.gf_low = gf_low;
        self.gf_high = gf_high;

    """
    TissueState is represented as a list of current tissue loadings (N2, He)
    """

    def cleared_tissue_state(self):
        gas = Gas.Air();
        return [ (gas[ 'fN2' ], gas[ 'fHe' ]) for i in range(self._n_tissues) ];

    @staticmethod
    def _updated_partial_pressure(pp_tissue, pp_ambient, halftime, duration):
        return pp_tissue + (1 - pow(.5, duration / halftime)) * (pp_ambient - pp_tissue);

    def updated_tissue_state(self, state, duration, p_amb, gas):
        pp_amb_n2 = p_amb * gas[ 'fN2' ];
        pp_amb_he = p_amb * gas[ 'fHe' ];
        new_state = [
            (Buhlmann._updated_partial_pressure(state[ i ][ 0 ], pp_amb_n2, self._halftimes[ 'N2' ][ i ], duration),
             Buhlmann._updated_partial_pressure(state[ i ][ 1 ], pp_amb_he, self._halftimes[ 'He' ][ i ], duration)
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
        a = self._coeffs[ 'N2' ][ 'a' ][ i ];
        b = self._coeffs[ 'N2' ][ 'b' ][ i ];
        pp_n2, pp_he = tissue_state_i;
        if pp_he > 0.0:
            # TODO test Trimix case
            # Trimix case
            a_he = self._coeffs[ 'He' ][ 'a' ][ i ];
            b_he = self._coeffs[ 'He' ][ 'b' ][ i ];
            a = pp_n2 / (pp_n2 + pp_he) * a + pp_he / (pp_n2 + pp_he) * a_he;
            b = pp_n2 / (pp_n2 + pp_he) * b + pp_he / (pp_n2 + pp_he) * b_he;
        return a, b;

    def _p_amb_tol_one_tissue(self, i, tissue_state_i):
        a, b = self._get_coeffs_a_b(i, tissue_state_i);
        p_compartment = sum(tissue_state_i);
        p_amb_tol = (p_compartment - a) * b;
        return p_amb_tol;

    def _p_amb_tol(self, tissue_state):
        return [ self._p_amb_tol_one_tissue(i, tissue_state[ i ]) for i in range(self._n_tissues) ];

    def _p_amb_tol_gf(self, tissue_state, gf):
        p_amb_tol = self._p_amb_tol(tissue_state);
        p_comptmt = [ sum(ts) for ts in tissue_state ];
        p = [ p_comptmt[ i ] - gf / 100 * (p_comptmt[ i ] - p_amb_tol[ i ])
              for i in range(self._n_tissues) ];
        return p;

    @staticmethod
    def _GF99_for_one_tissue(p_comptmt, p_amb, p_amb_tol):
        if p_comptmt == p_amb_tol:
            return 0.0;
        if p_comptmt < p_amb:
            # Ongassing
            return -1.0;
        return 100.0 * (p_comptmt - p_amb) / (p_comptmt - p_amb_tol);

    def _GF99(self, p_comptmt, p_amb, p_amb_tol):
        return max([ Buhlmann._GF99_for_one_tissue(p_comptmt[ i ], p_amb, p_amb_tol[ i ])
                     for i in range(self._n_tissues) ]);

    def _map_amb_to_gf_perc(self, p_first_stop):
        gf_low = self.gf_low
        gf_high = self.gf_high
        # At first stop, allowed supersaturation is GF_LOW % (eg. 35%)
        # At surfacing, allowed supersaturation is GF_HIGH % (eg. 70%)
        p_surface = 1.0;

        # So, at p_first_stop, allowed supersat is gf_low
        # and at p_surface, allowed supersat is gf_high
        # We return a function that linearly interpolates; is flat outside the bounds
        def m(p_amb):
            if p_amb > p_first_stop:
                return gf_low;
            elif p_amb < p_surface:
                return gf_high;
            else:
                return gf_high + (p_amb - p_surface) / (p_first_stop - p_surface) * (gf_low - gf_high);
        return m;

    def _time_to_stay_at_stop(self, p_amb, tissue_state, gas, amb_to_gf):
        # Returns both the time (integer) and the updated tissue_state.
        # TODO: Check performance. The "+1" is tricky. Binary search?
        # Straight computation is probably not feasible since a/b coeff's are dependent on pp
        # Straight computation could work for Nitrox, probably not for Trimix?
        p_amb_next_stop = Util.next_stop_Pamb(p_amb);

        gf99allowed = amb_to_gf(p_amb_next_stop);
        stop_length = 0;
        while stop_length < 500:    # Safety measure
            p_amb_tol = self._p_amb_tol(tissue_state);
            gf99 = self._GF99([ sum(ts) for ts in tissue_state ], p_amb_next_stop, p_amb_tol);
            if gf99 <= gf99allowed:
                break;
            stop_length += 1;
            tissue_state = self.updated_tissue_state( tissue_state, 1.0, p_amb, gas );
        return stop_length, tissue_state;

    def compute_deco_profile(self, tissue_state, p_target = 1.0, gf_now = None):
        # Returns triples depth, length, gas
        # Allowed to pass in gf_now in case we recompute part of the deco after it has already started
        # Determine ceiling, and allowed supersaturation at the various levels
        if gf_now is None:
            gf_now = self.gf_low;
        p_amb_tol_gfnow = self._p_amb_tol_gf(tissue_state, gf_now);
        p_ceiling = max(p_amb_tol_gfnow);
        assert p_ceiling < 100.0;  # Otherwise something very weird is happening
        p_first_stop = Util.Pamb_to_Pamb_stop(p_ceiling);  # First stop is rounded (to 3m)
        amb_to_gf = self._map_amb_to_gf_perc(p_first_stop);
        # Determine gas (TODO)
        gas = Gas.Air();
        # 'Walk' up
        result = [];
        p_now = p_first_stop;
        while p_now > p_target + 0.01:
            stoplength, tissue_state = self._time_to_stay_at_stop(p_now, tissue_state, gas, amb_to_gf);
            result.append( ( Util.Pamb_to_depth(p_now), stoplength, gas ) );
            p_now = Util.next_stop_Pamb(p_now);
        # Clean up the result
        result = [ x for x in result if x[1] != 0 ];
        return result, p_ceiling, amb_to_gf;

    def deco_info(self, tissue_state, depth, gf_now = None):
        p_amb = Util.depth_to_Pamb(depth);
        p_amb_tol = self._p_amb_tol(tissue_state);
        p_comptmt = [ sum(ts) for ts in tissue_state ];
        p_ceiling_99 = max(p_amb_tol);
        # GF99: how do compartment pressure, ambient pressure, tolerance compare
        # the % makes most sense if ambient pressure is between compartment pressure and tolerance
        # if ambient pressure is bigger than compartment pressure: ongassing
        gf99s = [ self._GF99_for_one_tissue(p_comptmt[ i ], p_amb, p_amb_tol[ i ])
                  for i in range(self._n_tissues) ];
        surfacegfs = [ self._GF99_for_one_tissue(p_comptmt[ i ], 1.0, p_amb_tol[ i ])
                       for i in range(self._n_tissues) ];
        result = {'Ceil99': Util.Pamb_to_depth(p_ceiling_99),
                  'GF99': round(max(gf99s), 1),
                  'SurfaceGF': round(max(surfacegfs), 1),
                  'allGF99s': gf99s
                  };

        # Below is about computing the decompression profile
        stops, p_ceiling, amb_to_gf = self.compute_deco_profile(tissue_state, gf_now = gf_now);
        result['Ceil'] = Util.Pamb_to_depth(p_ceiling);
        result['Stops'] = stops;
        result['amb_to_gf'] = amb_to_gf;

        # Done
        return result;


#
# Some testing functions
#
def test():
    bm = Buhlmann(35, 70);
    ts = bm.cleared_tissue_state();
    ts = bm.updated_tissue_state(ts, 20.0, 5.0, Gas.Trimix(21, 35));
    print(ts);
    di = bm.deco_info(ts, 40.0);
    print(di);
    # for d in [ 40.0, 10.0, 6.0, 3.0, 0.0 ]:
    #     di = bm.get_deco_state_info(ts, d);
    #     print('at %.1f: %s' % (d, di));


test();
