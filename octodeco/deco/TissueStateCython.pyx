# Please see LICENSE.md
array;
import array;

from . import Gas;

CONSTANT_ID = None;
cdef int N_TISSUES = 16;
cdef float[32] HALFTIMES;
cdef float[32] A_VALUES;
cdef float[32] B_VALUES;

# TissueState is represented as a list of current tissue loadings (N2, He)
class TissueState:
    def __init__(self, constants, empty=False):
        if constants is not None:
            TissueState.ensure_cython_constants(constants);
        self._ab = None;
        if not empty:
            self._set_init_state();

    def __repr__(self):
        return self._state.__repr__();

    def _set_init_state(self):
        gasc = TissueState.gas_to_cython(Gas.Air());
        self._state = array.array('f',[]); array.resize(self._state, 2*N_TISSUES);
        cdef float[:] cstate = self._state;
        cdef int i = 0, n = 16;
        while i < N_TISSUES:
            cstate[2*i] = gasc[0];
            cstate[2*i+1] = gasc[1];
            i += 1;


    #
    # Storing the constants in cython format
    #
    @staticmethod
    def _create_cython_constants(constants):
        global CONSTANT_ID;
        CONSTANT_ID = constants.ID;
        assert N_TISSUES == constants.N_TISSUES;
        cdef int i = 0;
        while i < N_TISSUES:
            # N2
            HALFTIMES[2*i] = constants.N2_HALFTIMES[i];
            A_VALUES[2*i]  = constants.N2_A_VALUES[i];
            B_VALUES[2*i]  = constants.N2_B_VALUES[i];
            #He
            HALFTIMES[2*i+1] = constants.HE_HALFTIMES[i];
            A_VALUES[2*i+1]  = constants.HE_A_VALUES[i];
            B_VALUES[2*i+1]  = constants.HE_B_VALUES[i];
            # Next
            i += 1;

    @staticmethod
    def ensure_cython_constants(constants):
        if CONSTANT_ID is None:
            TissueState._create_cython_constants(constants);
        # Only support one set of constants at run time
        assert CONSTANT_ID == constants.ID;

    @staticmethod
    def _create_gas_to_cython(gas):
        cdef float r[2];
        r[0] = gas['fN2'];
        r[1] = gas['fHe'];
        gas['cython_array'] = r;

    @staticmethod
    def gas_to_cython(gas):
        if 'cython_array' not in gas:
            TissueState._create_gas_to_cython(gas);
        return gas['cython_array'];

    #
    # Updating the tissue states
    #
    def updated_state(self, duration, p_amb, gas):
        r = TissueState(None, empty=True);
        r._state = array.array('f',[]); array.resize(r._state, 2*N_TISSUES);
        cdef float[:] coldstate = self._state;
        cdef float[:] cnewstate = r._state;
        gasc = TissueState.gas_to_cython(gas);
        cdef float pp_amb_n2 = p_amb * gasc[0];
        cdef float pp_amb_he = p_amb * gasc[1];
        cdef float cdur = duration;
        cdef int i = 0;
        cdef float tmp;
        while i < N_TISSUES:
            cnewstate[2*i] = coldstate[2*i] + ( 1 - 0.5 **( cdur/HALFTIMES[2*i]) ) * ( pp_amb_n2 - coldstate[2*i] );
            cnewstate[2*i+1] = coldstate[2*i+1] + ( 1 - 0.5 ** ( cdur/HALFTIMES[2*i+1]) ) * ( pp_amb_he - coldstate[2*i+1] );
            i += 1;
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

    def GF99_all_info(self, p_amb):
        gf99s = self.GF99s(p_amb);
        gf99 = max(0.0, max(gf99s));
        leading_tissue_i = gf99s.index(gf99);
        return gf99s, gf99, leading_tissue_i;

