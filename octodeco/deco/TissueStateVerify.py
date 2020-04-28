# Please see LICENSE.md
# This implementation designed to check the results of TissueState implementation

from . import TissueStateClassic;
from . import TissueStateNumpy;


class TissueState(TissueStateNumpy.TissueState):
    def __init__(self, constants):
        super().__init__(constants);
        self._old_style_constants = constants;

    def construct_classic(self):
        r = TissueStateClassic.TissueState(self._old_style_constants);
        r._state = [ ( self._state[0][i], self._state[1][i]) for i in range(self._n_tissues)];
        return r;

    def state_equal(self, classic_state):
        os_me = self.construct_classic();
        return os_me._state == classic_state._state;

    def updated_state(self, duration, p_amb, gas):
        r1 = super().updated_state(duration, p_amb, gas);
        r1.__class__ = TissueState;
        r1._old_style_constants = self._old_style_constants;
        r2 = self.construct_classic().updated_state(duration, p_amb, gas);
        assert r1.state_equal(r2);
        print('updated_state: OK')
        return r1;

    def GF99(self, p_amb):
        r1 = super().GF99(p_amb);
        r2 = self.construct_classic().GF99(p_amb);
        assert r1 == r2;
        return r1;

    def p_ceiling_for_amb_to_gf(self, amb_to_gf):
        r1 = super().p_ceiling_for_amb_to_gf(amb_to_gf);
        r2 = self.construct_classic().p_ceiling_for_amb_to_gf(amb_to_gf);
        assert r1 == r2;
        return r1;

    def p_ceiling_for_gf_now(self, gf_now):
        r1 = super().p_ceiling_for_gf_now(gf_now)
        r2 = self.construct_classic().p_ceiling_for_gf_now(gf_now);
        assert r1 == r2;
        print('ceiling_gf_now: OK');
        return r1;
