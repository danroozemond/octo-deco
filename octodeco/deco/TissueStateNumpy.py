# Please see LICENSE.md
from collections import namedtuple

import numpy as np;

from . import Gas;

ZHL16ConstantsNP = namedtuple('ZHL16ConstantsNP', [
    'ID', 'N_TISSUES', 'HALFTIMES', 'A_VALUES', 'B_VALUES']);
CONSTANTS = {};


class TissueState:
    def __init__(self, constants, empty=False):
        self._constants = TissueState.ensure_numpy_constants(constants);
        self._n_tissues = self._constants.N_TISSUES;
        if not empty:
            self._state = TissueState.gas_to_numpy(Gas.Air()).repeat(self._n_tissues,axis=1);

    def __repr__(self):
        return self._state.__repr__();

    def __copy__(self):
        r = TissueState(self._constants, empty=True);
        r._state = self._state;
        return r;

    def copy(self):
        return self.__copy__();

    #
    # Storing the constants in numpy format
    #
    @staticmethod
    def ensure_numpy_constants(constants):
        if constants.ID not in CONSTANTS:
            CONSTANTS[constants.ID] = ZHL16ConstantsNP(
                ID = constants.ID,
                N_TISSUES = constants.N_TISSUES,
                HALFTIMES = np.array([ constants.N2_HALFTIMES, constants.HE_HALFTIMES], dtype='float64'),
                A_VALUES = np.array([ constants.N2_A_VALUES, constants.HE_A_VALUES], dtype='float64'),
                B_VALUES = np.array([ constants.N2_B_VALUES, constants.HE_B_VALUES], dtype='float64')
            )
        return CONSTANTS[constants.ID];

    @staticmethod
    def gas_to_numpy(gas):
        return np.array([[gas[ 'fN2' ],gas[ 'fHe' ]]], dtype='float64').transpose();

    #
    # Updating the tissue states
    #
    def _updated_partial_pressure(self, pp_alv, duration):
        # pp_alv should be a column vector
        return self._state + (1 - pow(.5, duration / self._constants.HALFTIMES)) * ( pp_alv - self._state);

    def updated_state(self, duration, p_amb, gas):
        r = TissueState(self._constants, empty=True);
        pp_alv = p_amb * TissueState.gas_to_numpy(gas);
        r._state = self._updated_partial_pressure(pp_alv, duration);
        return r;

    #
    # Workmann / Buhlmann coefficients (retrieval nontrivial in Trimix case)
    #
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
    def _get_coeffs_a_b_all(self):
        # a and b values are linear combinations depending on current
        # partial pressures N2/He
        totalpp = self._state.sum(axis=0);
        a = ((self._state / totalpp) * self._constants.A_VALUES).sum(axis = 0);
        b = ((self._state / totalpp) * self._constants.B_VALUES).sum(axis = 0);
        return a,b;

    def _workmann_m0_all(self, p_amb):
        a,b = self._get_coeffs_a_b_all();
        m0 = a + p_amb / b;
        return m0;

    #
    # p_ceiling for various scenarios
    #
    def p_ceiling_for_gf_now(self, gf_now):
        # Derived from _GF99_new as defined below
        gff = gf_now / 100.0;
        a,b = self._get_coeffs_a_b_all();
        p_ceilings = ( self._state.sum(axis=0) - a*gff ) / ( gff/b - gff + 1 );
        return p_ceilings.max();

    def p_ceiling_for_amb_to_gf(self, amb_to_gf):
        # Binary search again
        #   p0 < h < p1
        #   too_high_gf(p0) > 0
        #   too_high_gf(p1) < 0
        def too_high_gf(p_amb):
            gf_now = amb_to_gf(p_amb);
            return self.GF99(p_amb) - gf_now;
        p0 = 1.0;
        p1 = 99.0;
        if too_high_gf(p0) < 0.0:
            return 1.0;
        while p1 - p0 > 0.001:
            h = p0 + ( p1-p0 )/2;
            if too_high_gf(h) > 0:
                p0 = h;
            else:
                p1 = h;
        return p1;

    #
    # GF99
    #
    def GF99s(self, p_amb):
        m0s = self._workmann_m0_all(p_amb);
        gf99s = 100.0 * ( self._state.sum(axis=0) - p_amb ) / ( m0s - p_amb );
        return gf99s;

    def GF99(self, p_amb):
        return max(0.0, self.GF99s(p_amb).max());

