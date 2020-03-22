import Gas, BuhlmannConstants;

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
    def init_tissue_state(self):
        gas = Gas.Air();
        return [ (gas['fN2'], gas['fHe'] ) for i in range(self._n_tissues) ];


#
# Some testing functions
#
bm = Buhlmann();
ts = bm.init_tissue_state();
print(ts);
