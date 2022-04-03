# Please see LICENSE.md
#
# I apologize, this has become an awful file to look at.

from cpython cimport array;
import array;

from . import Gas, Util;

CONSTANT_ID = None;
cdef int N_TISSUES = 16;
cdef float[32] HALFTIMES;
cdef float[32] A_VALUES;
cdef float[32] B_VALUES;

# TissueState is represented as a list of current tissue loadings (N2, He)
class TissueState:
    def __init__(self, constants, rq, empty=False):
        if constants is not None:
            TissueState.ensure_cython_constants(constants);
        self._ab = None;
        self._rq = rq;
        if not empty:
            self._set_init_state();

    def __repr__(self):
        return self._state.__repr__();

    def _set_init_state(self):
        gasc = TissueState.gas_to_cython(Gas.Air());
        self._state = array.array('f',[]); array.resize(self._state, 2*N_TISSUES);
        cdef p_alv = self.amb_to_alv(Util.SURFACE_PRESSURE);
        cdef float[:] cstate = self._state;
        cdef int i = 0, n = 16;
        while i < N_TISSUES:
            cstate[2*i] = p_alv * gasc[0];
            cstate[2*i+1] = p_alv * gasc[1];
            i += 1;

    def print_pps(self):
        return ' '.join([ '{:.2f}'.format(self._state[2*i] + self._state[2*i+1]) for i in range(N_TISSUES) ]);

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
    # p_alv = p_amb - p_h2o - (1-RQ)/RQ * p_co2
    # where p_h2o = 0.0627, p_co2 = 0.0534, and RQ = 0.8, 0.9, or 1.0 depending on conservatism
    # See Deco for Divers, pages 177/178
    #
    def amb_to_alv(self, p_amb):
        p_alv = p_amb - 0.0627 + ((1-self._rq)/self._rq)*0.0534;
        return p_alv;

    def updated_state(self, duration, p_amb, gas):
        r = TissueState(None, self._rq, empty=True);
        r._state = array.array('f',[]); array.resize(r._state, 2*N_TISSUES);
        cdef float[:] coldstate = self._state;
        cdef float[:] cnewstate = r._state;
        gasc = TissueState.gas_to_cython(gas);
        cdef p_alv = self.amb_to_alv(p_amb);
        cdef float pp_alv_n2 = p_alv * gasc[0];
        cdef float pp_alv_he = p_alv * gasc[1];
        cdef float cdur = duration;
        cdef int i = 0;
        cdef float tmp;
        while i < N_TISSUES:
            cnewstate[2*i] = coldstate[2*i] + ( 1 - 0.5 **( cdur/HALFTIMES[2*i]) ) * ( pp_alv_n2 - coldstate[2*i] );
            cnewstate[2*i+1] = coldstate[2*i+1] + ( 1 - 0.5 ** ( cdur/HALFTIMES[2*i+1]) ) * ( pp_alv_he - coldstate[2*i+1] );
            i += 1;
        return r;

    def p_tissue(self, i):
        # Return inert gas pressure in tissue i
        return self._state[2*i] + self._state[2*i+1];

    def p_tissue_n2_he(self, i):
        return self._state[2*i], self._state[2*i+1];

    #
    # For computing integral supersaturation (as defined by Simon Mitchell)
    #
    def abs_supersat(self, p_amb):
        cdef float r = 0;
        cdef float p_tissue = 0;
        cdef float[:] cstate = self._state;
        cdef int i = 0;
        while i < N_TISSUES:
            p_tissue = cstate[2*i] + cstate[2*i+1];
            if p_tissue > p_amb:
                r += p_tissue - p_amb;
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
    def _set_coeffs_a_b(self):
        cdef float pp;
        cdef float[:] cstate = self._state;
        cdef int i = 0;
        a = array.array('f', [ ]); array.resize(a, N_TISSUES);
        b = array.array('f', [ ]); array.resize(b, N_TISSUES);
        cdef float[:] ca = a;
        cdef float[:] cb = b;
        while i < N_TISSUES:
            pp = cstate[2*i] + cstate[2*i+1];
            ca[i] = (cstate[2*i]/pp)*A_VALUES[2*i] + (cstate[2*i+1]/pp)*A_VALUES[2*i+1];
            cb[i] = (cstate[2*i]/pp)*B_VALUES[2*i] + (cstate[2*i+1]/pp)*B_VALUES[2*i+1];
            i += 1;
        # Do stuff
        self._ab = (a,b);

    def _get_coeffs_a_b(self):
        if self._ab is None:
            self._set_coeffs_a_b();
        return self._ab;

    def _workmann_m0(self, p_amb):
        m = array.array('f', [ ]); array.resize(m, N_TISSUES);
        a, b = self._get_coeffs_a_b();
        cdef float[:] cm = m;
        cdef float[:] ca = a;
        cdef float[:] cb = b;
        cdef float cpamb = p_amb;
        cdef int i = 0;
        while i < N_TISSUES:
            m[i] = ca[i] + cpamb / cb[i];
            i += 1;
        return m;

    def _m_values_gf_proper(self, amb_to_gf, p_amb):
        cdef float cpamb = p_amb;
        cdef float cpsu = amb_to_gf.p_surface;
        cdef float cpfs = amb_to_gf.p_first_stop;
        cdef float cgf_high_f = amb_to_gf.gf_high / 100.0;
        cdef float cgf_low_f = amb_to_gf.gf_low / 100.0;
        cdef float[:] cm_su = self._workmann_m0(cpsu);
        cdef float[:] cm_fs = self._workmann_m0(cpfs);
        assert cpsu <= cpamb and cpamb <= cpfs;
        mgf = array.array('f', [ ]); array.resize(mgf, N_TISSUES);
        cdef float[:] cmgf = mgf;
        cdef int i = 0;
        cdef float m_at_gf_high, m_at_gf_low;
        while i < N_TISSUES:
            m_at_gf_high = cpsu + cgf_high_f * ( cm_su[i] - cpsu );
            m_at_gf_low =  cpfs + cgf_low_f  * ( cm_fs[i] - cpfs );
            cmgf[i] = m_at_gf_high + (cpamb - cpsu) / (cpfs-cpsu) * ( m_at_gf_low - m_at_gf_high );
            i += 1;
        return mgf;

    def _m_values_gf_point(self, p_amb, gf_value):
        m = self._workmann_m0(p_amb);
        cdef float[:] cm = m;
        mgf = array.array('f', [ ]); array.resize(mgf, N_TISSUES);
        cdef float[:] cmgf = mgf;
        cdef int i = 0;
        cdef float gff = gf_value / 100.0;
        while i < N_TISSUES:
            cmgf[i] = p_amb + gff * (cm[i] - p_amb);
            i += 1;
        return mgf;

    def _m_values_gf(self, amb_to_gf, p_amb):
        # here do the proper thing if in range, otherwise fixed
        cdef float cpsu = amb_to_gf.p_surface;
        cdef float cpfs = amb_to_gf.p_first_stop;
        if amb_to_gf.p_surface == amb_to_gf.p_first_stop:
            return self._m_values_gf_point(p_amb, amb_to_gf.gf_high);
        elif p_amb <= amb_to_gf.p_surface:
            return self._m_values_gf_point(p_amb, amb_to_gf.gf_high);
        elif amb_to_gf.p_first_stop <= p_amb:
            return self._m_values_gf_point(p_amb, amb_to_gf.gf_low);
        else:
            # Actually compute the GF line as defined
            return self._m_values_gf_proper(amb_to_gf, p_amb);

    def max_over_supersat(self, amb_to_gf, p_amb):
        cdef float[:] cmgf = self._m_values_gf(amb_to_gf, p_amb);
        cdef float[:] cstate = self._state;
        cdef float over_supersat;
        cdef int i = 0;
        while i < N_TISSUES:
            over_supersat = cstate[2*i] + cstate[2*i+1] - cmgf[i];
            if i == 0 or over_supersat > r:
                r = over_supersat;
            i += 1;
        return r;

    #
    # p_ceiling for various scenarios
    #
    def p_ceiling_for_gf_now(self, gf_now):
        # Derived from _GF99 as defined below
        cdef float gff = gf_now / 100.0;
        cdef float pceil = -100;
        cdef float pceil_i;
        cdef int i = 0;
        a,b = self._get_coeffs_a_b();
        cdef float[:] ca = a;
        cdef float[:] cb = b;
        cdef float[:] cstate = self._state;
        while i < N_TISSUES:
            pceil_i = ( cstate[2*i] + cstate[2*i+1] - a[i]*gff) / ( gff / b[i] - gff + 1);
            if pceil_i > pceil:
                pceil = pceil_i;
            i += 1;
        return pceil;

    def p_ceiling_for_amb_to_gf(self, amb_to_gf):
        # Binary search again
        #   p0 < h < p1
        #   too_high_gf(p0) > 0
        #   too_high_gf(p1) < 0
        p0 = Util.SURFACE_PRESSURE;
        p1 = 99.0;
        if self.max_over_supersat(amb_to_gf, p0) < 0.0:
            return p0;
        while p1 - p0 > 0.001:
            h = p0 + ( p1-p0 )/2;
            if self.max_over_supersat(amb_to_gf, h) > 0:
                p0 = h;
            else:
                p1 = h;
        return p1;

    #
    # GF99
    #
    def GF99s(self, p_amb):
        m = self._workmann_m0(p_amb);
        cdef float[:] cm = m;
        cdef float[:] cstate = self._state;
        cdef float cpamb = p_amb;
        cdef int i = 0;
        cdef float r;
        res = [];
        while i < N_TISSUES:
            r = 100.0 * ( cstate[2*i] + cstate[2*i+1] - cpamb ) / ( cm[i] - cpamb );
            res.append(r);
            i += 1;
        return res;

    def GF99(self, p_amb):
        a, b = self._get_coeffs_a_b();
        cdef float[:] ca = a;
        cdef float[:] cb = b;
        cdef float[:] cstate = self._state;
        cdef float cpamb = p_amb;
        cdef float gf99 = 0.0;
        cdef float r = 0.0;
        cdef m0 = 0.0;
        cdef int i = 0;
        while i < N_TISSUES:
            m0 = a[i] + cpamb / b[i];
            r = 100.0 * (cstate[ 2 * i ] + cstate[ 2 * i + 1 ] - cpamb) / (m0 - cpamb);
            if r > gf99:
                gf99 = r;
            i += 1;
        return gf99;

    def GF99_all_info(self, p_amb):
        gf99s = self.GF99s(p_amb);
        gf99 = max(gf99s);
        leading_tissue_i = gf99s.index(gf99);
        return gf99s, max(0.0, gf99), leading_tissue_i;



