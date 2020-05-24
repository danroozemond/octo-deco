# Please see LICENSE.md
# This class designed to check the results of TissueState implementation

from . import TissueStateClassic;
from . import TissueStateCython;


class TissueState(TissueStateCython.TissueState):
    def __init__(self, constants):
        super().__init__(constants);
        self._n_tissues = constants.N_TISSUES;
        self._old_style_constants = constants;

    def construct_classic(self):
        r = TissueStateClassic.TissueState(self._old_style_constants, self._rq);
        r._state = [ ( self._state[2*i], self._state[2*i+1]) for i in range(self._n_tissues)];
        return r;

    def state_equal(self, classic_state):
        s1 = self.construct_classic()._state;
        s2 = classic_state._state;
        diff = max([ max([ abs(s1[i][j]-s2[i][j]) for j in range(2) ]) for i in range(self._n_tissues) ]);
        return diff < 1e-4;

    def updated_state(self, duration, p_amb, gas):
        r1 = super().updated_state(duration, p_amb, gas);
        r1.__class__ = TissueState;
        r1._old_style_constants = self._old_style_constants;
        r1._n_tissues = self._n_tissues;
        r2 = self.construct_classic().updated_state(duration, p_amb, gas);
        assert r1.state_equal(r2);
        return r1;

    def GF99(self, p_amb):
        r1 = super().GF99(p_amb);
        r2 = self.construct_classic().GF99(p_amb);
        assert abs(r1-r2) < 1e-4;
        return r1;

    def p_ceiling_for_amb_to_gf(self, amb_to_gf):
        r1 = super().p_ceiling_for_amb_to_gf(amb_to_gf);
        r2 = self.construct_classic().p_ceiling_for_amb_to_gf(amb_to_gf);
        assert abs(r1-r2) < 1e-5;
        return r1;

    def p_ceiling_for_gf_now(self, gf_now):
        r1 = super().p_ceiling_for_gf_now(gf_now)
        r2 = self.construct_classic().p_ceiling_for_gf_now(gf_now);
        assert abs(r1-r2) < 1e-5;
        return r1;
