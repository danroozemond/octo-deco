# Please see LICENSE.md
import Util


class DivePoint:
    def __init__(self, time, depth, gas, prev):
        self.time = time;
        self.depth = depth;
        self.p_amb = Util.depth_to_Pamb(depth);
        self.gas = gas;
        self.tissue_state = None;
        self.deco_info = None;
        self.is_deco_stop = False;
        self.is_interpolated_point = False;
        self.prev = prev;

    def __repr__(self):
        return '%.1f:%dm' % (self.time, self.depth);

    @staticmethod
    def dataframe_columns_deco_info():
        return [ 'FirstStop', 'Ceil', 'Ceil99', 'GF99', 'SurfaceGF', 'LeadingTissueIndex', 'TTS', 'NDL' ];

    @staticmethod
    def dataframe_columns():
        return [ 'time', 'depth', 'gas', 'ppO2' ] \
                + DivePoint.dataframe_columns_deco_info() \
                + [ 'Stops' ];

    def repr_for_dataframe(self):
        r = [ self.time, self.depth, str(self.gas), self.gas['fO2'] * self.p_amb ];
        if self.deco_info is not None:
            r += [ self.deco_info[n] for n in DivePoint.dataframe_columns_deco_info() ];
            r += [ Util.stops_to_string( self.deco_info['Stops'] ) ];
        return r;

    def duration(self):
        if self.prev is None:
            return 0.0;
        return self.time - self.prev.time;

    def set_cleared_tissue_state(self, deco_model):
        self.tissue_state = deco_model.cleared_tissue_state();

    def set_updated_tissue_state(self, deco_model):
        assert self.time >= self.prev.time;  # Otherwise divepoints are in a broken sequence
        assert self.prev is not None;
        self.tissue_state = deco_model.updated_tissue_state(
            self.prev.tissue_state,
            self.duration(),
            ( self.p_amb + self.prev.p_amb ) / 2,
            self.gas );

    def set_updated_deco_info(self, deco_model, gases, amb_to_gf = None ):
        self.deco_info = deco_model.deco_info(self.tissue_state, self.depth, self.gas, gases, amb_to_gf = amb_to_gf );


