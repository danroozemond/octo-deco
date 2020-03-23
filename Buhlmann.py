import BuhlmannConstants
import Gas
import Util

"""
Buhlmann class contains all essential logic for deco model
"""


class Buhlmann:
    # TODO: This is where gradient factors should eventually be added
    def __init__(self):
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
        if p_amb > p_comptmt:
            # Ongassing
            return -1;
        return 100.0 * (p_comptmt - p_amb) / (p_comptmt - p_amb_tol);

    def get_deco_state_info(self, tissue_state, depth):
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

        return {'ceiling': Util.Pamb_to_depth(p_ceiling),
                'GF99': round(max(gf99s), 1),
                'SurfaceGF': round(max(surfacegfs), 1)
                };


#
# Some testing functions
#
def test():
    bm = Buhlmann();
    ts = bm.cleared_tissue_state();
    ts = bm.updated_tissue_state(ts, 10.0, 40.0, Gas.Trimix(21, 35));
    print(ts);
    for d in [ 40.0, 10.0, 6.0, 3.0, 0.0 ]:
        di = bm.get_deco_state_info(ts, d);
        print('at %.1f: %s' % (d, di));


test();
