# Please see LICENSE.md
from collections import namedtuple

import numpy as np;

from . import Gas;

ZHL16ConstantsNP = namedtuple('ZHL16ConstantsNP', [
    'ID', 'N_TISSUES', 'HALFTIMES', 'A_VALUES', 'B_VALUES']);
CONSTANTS = {};


class TissueState:
    def __init__(self, constants):
        self._constants = TissueState.ensure_numpy_constants(constants);
        self._n_tissues = self._constants.N_TISSUES;
        gas = Gas.Air();
        self._state = list(map( lambda i: (gas[ 'fN2' ], gas[ 'fHe' ]), range(self._n_tissues)));
        # b = np.array([1.2, 3.5, 5.1], dtype='float64');

    def __repr__(self):
        return self._state.__repr__();

    def __copy__(self):
        r = TissueState(self._constants);
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
                B_VALUES = np.array([ constants.HE_A_VALUES, constants.HE_B_VALUES], dtype='float64')
            )
        return CONSTANTS[constants.ID];

    #
    # Updating the tissue states
    #
    @staticmethod
    def _updated_partial_pressure(pp_tissue, pp_alveolar, halftime, duration):
        return pp_tissue + (1 - pow(.5, duration / halftime)) * (pp_alveolar - pp_tissue);

    def updated_state(self, duration, p_amb, gas):
        r = self.copy();
        pp_amb_n2 = p_amb * gas[ 'fN2' ];
        pp_amb_he = p_amb * gas[ 'fHe' ];
        r._state = [ (
            self._updated_partial_pressure(self._state[i][0], pp_amb_n2, self._constants.N2_HALFTIMES[ i ], duration),
            self._updated_partial_pressure(self._state[i][1], pp_amb_he, self._constants.HE_HALFTIMES[ i ], duration)
        ) for i in range(self._n_tissues) ];
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
    def _get_coeffs_a_b(self, i):
        a = self._constants.N2_A_VALUES[ i ];
        b = self._constants.N2_B_VALUES[ i ];
        pp_n2, pp_he = self._state[i];
        if pp_he > 0.0:
            # Trimix case
            a_he = self._constants.HE_A_VALUES[ i ];
            b_he = self._constants.HE_B_VALUES[ i ];
            a = pp_n2 / (pp_n2 + pp_he) * a + pp_he / (pp_n2 + pp_he) * a_he;
            b = pp_n2 / (pp_n2 + pp_he) * b + pp_he / (pp_n2 + pp_he) * b_he;
        return a, b;

    def _workmann_m0(self, p_amb, i):
        a, b = self._get_coeffs_a_b(i);
        m0 = a + p_amb / b;
        return m0;

    #
    # p_ceiling for various scenarios
    #
    def p_ceiling_for_gf_now(self, gf_now):
        # Derived from _GF99_new as defined below
        gff = gf_now / 100.0;

        # Returns the ceiling for one particular tissue
        def for_one(i):
            a, b = self._get_coeffs_a_b(i);
            p_amb = (sum(self._state[ i ]) - a * gff) / (gff / b - gff + 1);
            return p_amb;

        p_ceilings = [ for_one(i) for i in range(self._n_tissues) ];
        return max(p_ceilings);

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
        def for_one(i):
            m0 = self._workmann_m0(p_amb, i);
            return 100.0 * (sum(self._state[ i ]) - p_amb) / (m0 - p_amb);
        return [ max(0.0, for_one(i)) for i in range(self._n_tissues) ];

    def GF99(self, p_amb):
        return max(0.0, max(self.GF99s(p_amb)));
