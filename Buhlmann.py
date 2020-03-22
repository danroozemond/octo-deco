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
        return [ (gas['fN2'], gas['fHe'] ) for i in range(self._n_tissues) ];

    @staticmethod
    def _updated_partial_pressure( pp_tissue, pp_ambient, halftime, duration ):
        return pp_tissue + ( 1 - pow(.5, duration/halftime ) )*( pp_ambient - pp_tissue );

    def updated_tissue_state(self, state, duration, depth, gas ):
        p_amb = Util.depth_to_Pamb(depth);
        pp_amb_n2 = p_amb * gas['fN2'];
        pp_amb_he = p_amb * gas['fHe'];
        new_state = [
            ( Buhlmann._updated_partial_pressure( state[i][0], pp_amb_n2, self._halftimes['N2'][i], duration ),
              Buhlmann._updated_partial_pressure( state[i][1], pp_amb_he, self._halftimes['He'][i], duration ),
            ) for i in range(self._n_tissues) ];
        return new_state;


#
# Some testing functions
#
bm = Buhlmann();
ts = bm.cleared_tissue_state();
ts = bm.updated_tissue_state( ts, 10.0, 40.0, Gas.Trimix(21,35));
