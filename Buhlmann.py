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

    """
    TissueState is represented as a list of current tissue loadings (N2, He)
    """

    def cleared_tissue_state(self):
        gas = Gas.Air();
        return [ (gas[ 'fN2' ], gas[ 'fHe' ]) for i in range(self._n_tissues) ];

    @staticmethod
    def _updated_partial_pressure(pp_tissue, pp_ambient, halftime, duration):
        return pp_tissue + (1 - pow(.5, duration / halftime)) * (pp_ambient - pp_tissue);

    def updated_tissue_state(self, state, duration, depth, gas):
        p_amb = Util.depth_to_Pamb(depth);
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

    def _get_p_amb_tol(self, i, tissue_state_i):
        a, b = self._get_coeffs_a_b(i, tissue_state_i);
        p_compartment = sum(tissue_state_i);
        p_amb_tol = (p_compartment - a) * b;
        return p_amb_tol;

    @staticmethod
    def _get_GF99_for_one_tissue(p_comptmt, p_amb, p_amb_tol):
        if p_comptmt == p_amb_tol:
            return 0.0;
        if p_comptmt < p_amb:
            # Ongassing
            return -1.0;
        return 100.0 * (p_comptmt - p_amb) / (p_comptmt - p_amb_tol);

    def _get_map_amb_to_gf_perc(self,  p_comptmt, p_amb_tol):
        gf_low  = 35; # self.gf_low
        gf_high = 70; # self.gf_high
        # At first stop, allowed supersaturation is GF_LOW % (eg. 35%)
        # At surfacing, allowed supersaturation is GF_HIGH % (eg. 70%)
        p_amb_tol_gflow = [ p_comptmt[ i ] - gf_low / 100 * (p_comptmt[ i ] - p_amb_tol[ i ]) for i in
                            range(self._n_tissues) ];
        p_ceiling = max(p_amb_tol_gflow);
        # Round the first stop
        p_first_stop = Util.depth_to_Pamb(Util.Pamb_to_depth(p_ceiling, 3));
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
                return gf_high + (p_amb - p_surface)/(p_first_stop - p_surface) * ( gf_low - gf_high );

        return m;

    def get_deco_info(self, tissue_state, depth, stateOnly=True):
        p_amb = Util.depth_to_Pamb(depth);
        p_amb_tol = [ self._get_p_amb_tol(i, tissue_state[ i ]) for i in range(self._n_tissues) ];
        p_comptmt = [ sum(ts) for ts in tissue_state ];
        p_ceiling = max(p_amb_tol);
        # GF99: how do compartment pressure, ambient pressure, tolerance compare
        # the % makes most sense if ambient pressure is between compartment pressure and tolerance
        # if ambient pressure is bigger than compartment pressure: ongassing
        gf99s = [ self._get_GF99_for_one_tissue(p_comptmt[ i ], p_amb, p_amb_tol[ i ])
                  for i in range(self._n_tissues) ];
        surfacegfs = [ self._get_GF99_for_one_tissue(p_comptmt[ i ], 1.0, p_amb_tol[ i ])
                       for i in range(self._n_tissues) ];
        result = { 'Ceil99': Util.Pamb_to_depth(p_ceiling),
                    'GF99': round(max(gf99s), 1),
                    'SurfaceGF': round(max(surfacegfs), 1),
                    'allGF99s': gf99s
                    };
        if stateOnly:
            return result;

        # Below is about computing the decompression profile
        print(result)

        m = self._get_map_amb_to_gf_perc( p_comptmt, p_amb_tol );
        for depth in range(30,-6,step := -3):
            print("depth: %.1f, allowed supersat: %.1f" % ( depth, m(Util.depth_to_Pamb(depth))));

        # Done
        return result;


#
# Some testing functions
#
def test():
    bm = Buhlmann(35,70);
    ts = bm.cleared_tissue_state();
    ts = bm.updated_tissue_state(ts, 10.0, 40.0, Gas.Trimix(21, 35));
    print(ts);
    di = bm.get_deco_info(ts, 40.0, stateOnly=False);
    print(di);
    # for d in [ 40.0, 10.0, 6.0, 3.0, 0.0 ]:
    #     di = bm.get_deco_state_info(ts, d);
    #     print('at %.1f: %s' % (d, di));

test();
