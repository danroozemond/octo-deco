# Please see LICENSE.md
# This implementation designed to check the results of TissueState implementation
import copy;

from . import TissueStateClassic;
from . import TissueStateNumpy;


class TissueState(TissueStateNumpy.TissueState):
    def __init__(self, constants):
        super(TissueStateNumpy.TissueState, self).__init__(constants);

    def construct_classic(self):
        r = TissueStateClassic.TissueState(self._constants);
        r._state = copy.copy(self._state);
        return r;

    def updated_state(self, duration, p_amb, gas):
        r = super(TissueStateNumpy.TissueState, self).updated_state(duration, p_amb, gas);
        r.__class__ = TissueState;
        return r;

    def GF99(self, p_amb):
        r1 = super().GF99(p_amb);
        r2 = self.construct_classic().GF99(p_amb);
        assert r1 == r2;
        return r1;
