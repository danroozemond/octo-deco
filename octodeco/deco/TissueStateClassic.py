# Please see LICENSE.md
from . import Gas;



"""
TissueState is represented as a list of current tissue loadings (N2, He)
"""
class TissueState():
    def __init__(self, constants):
        gas = Gas.Air();
        self._constants = constants;
        self._n_tissues = self._constants.N_TISSUES;
        self._state = [ (gas[ 'fN2' ], gas[ 'fHe' ]) for i in range(self._n_tissues) ];

    def __repr__(self):
        return self._state.__repr__();

    def __copy__(self):
        r = TissueState(self._constants);
        r._state = self._state;
        return r;

    def copy(self):
        return self.__copy__();

    @staticmethod
    def _updated_partial_pressure(pp_tissue, pp_alveolar, halftime, duration):
        return pp_tissue + (1 - pow(.5, duration / halftime)) * (pp_alveolar - pp_tissue);

    def updated_tissue_state(self, state, duration, p_amb, gas):
        pp_amb_n2 = p_amb * gas[ 'fN2' ];
        pp_amb_he = p_amb * gas[ 'fHe' ];
        new_state = [ (
            self._updated_partial_pressure(state[ i ][ 0 ], pp_amb_n2, self._constants.N2_HALFTIMES[ i ], duration),
            self._updated_partial_pressure(state[ i ][ 1 ], pp_amb_he, self._constants.HE_HALFTIMES[ i ], duration),
        ) for i in range(self._n_tissues) ];
        return new_state;