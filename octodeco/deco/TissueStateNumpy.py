# Please see LICENSE.md
from collections import namedtuple

import numpy as np;

from . import Gas, Util;

ZHL16ConstantsNP = namedtuple('ZHL16ConstantsNP', [
    'ID', 'N_TISSUES', 'HALFTIMES', 'A_VALUES', 'B_VALUES']);
CONSTANTS = {};

NP_FLOAT_DATATYPE = np.float64;


class TissueState:
    def __init__(self, constants, empty=False):
        self._constants = TissueState.ensure_numpy_constants(constants);
        self._n_tissues = self._constants.N_TISSUES;
        self._ab = None;
        if not empty:
            self._state = TissueState.gas_to_numpy(Gas.Air()).repeat(self._n_tissues,axis=1);

    def __repr__(self):
        return self._state.__repr__();

    def __copy__(self):
        r = TissueState(self._constants, empty=True);
        r._state = self._state;
        r._ab = self._ab;
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
                HALFTIMES = np.array([ constants.N2_HALFTIMES, constants.HE_HALFTIMES], dtype=NP_FLOAT_DATATYPE),
                A_VALUES = np.array([ constants.N2_A_VALUES, constants.HE_A_VALUES], dtype=NP_FLOAT_DATATYPE),
                B_VALUES = np.array([ constants.N2_B_VALUES, constants.HE_B_VALUES], dtype=NP_FLOAT_DATATYPE)
            )
        return CONSTANTS[constants.ID];

    @staticmethod
    def gas_to_numpy(gas):
        if 'np_array' not in gas:
            r = np.array([[gas[ 'fN2' ],gas[ 'fHe' ]]], dtype=NP_FLOAT_DATATYPE).transpose();
            gas['np_array'] = r;
        return gas['np_array'];

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

    def p_tissue(self, i):
        ## did not implement yet
        return None;

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
        if self._ab is not None:
            return self._ab;
        # a and b values are linear combinations depending on current
        # partial pressures N2/He
        lcpp = self._state / (self._state.sum(axis=0));
        a = (lcpp * self._constants.A_VALUES).sum(axis = 0);
        b = (lcpp * self._constants.B_VALUES).sum(axis = 0);
        self._ab = (a,b);
        return a, b;

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
        p0 = Util.SURFACE_PRESSURE;
        p1 = 99.0;
        if too_high_gf(p0) < 0.0:
            return p0;
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
        r = self.GF99s(p_amb).max();
        return r if r >= 0.0 else 0.0;

    def GF99_all_info(self, p_amb):
        gf99s = self.GF99s(p_amb);
        return gf99s, max(0.0, gf99s.max()), gf99s.argmax();


def construct_numpy_from_classic(tissue_state, classic_constants):
    r = TissueState(classic_constants, empty = True);
    r._state = np.array(tissue_state, dtype=NP_FLOAT_DATATYPE).transpose();
    return r;
