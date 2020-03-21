import Gas, BuhlmannConstants;

"""
Buhlmann class contains all essential logic for deco model
"""
class Buhlmann:
    # TODO: This is where gradient factors should eventually be added
    def __init__(self):
        self._halftimes = { 'N2': BuhlmannConstants.ZHL_16C_N2_HALFTIMES,
                            'He': BuhlmannConstants.ZHL_16C_HE_HALFTIMES };

    """
    TissueState is represented as a dict mapping int to float (half time to pp)
    N2 and He have separate states
    """
    def init_tissue_state(self, inert_gas):
        gas = Gas.Air();
        return {ht: gas[ 'f' + inert_gas ] for ht in self._halftimes[inert_gas]};


##
## Some testing functions
##
bm = Buhlmann();
ts = bm.init_tissue_state('N2');
print(ts);
