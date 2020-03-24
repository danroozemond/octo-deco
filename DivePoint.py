import Util


class DivePoint:
    def __init__(self, time, depth, gas):
        self.time = time;
        self.depth = depth;
        self.gas = gas;
        self.tissue_state = None;
        self.deco_info = None;

    def __repr__(self):
        return '%.1f:%dm' % (self.time, self.depth);

    @staticmethod
    def dataframe_columns():
        return [ 'time', 'depth', 'gas', 'ppO2',
                 'Ceil', 'GF99', 'SurfaceGF',
                 'Stops' ];

    def repr_for_dataframe(self):
        r = [ self.time, self.depth, str(self.gas), self.gas['fO2'] * Util.depth_to_Pamb(self.depth) ];
        if self.deco_info is not None:
            r += [ self.deco_info[n] for n in [ 'Ceil', 'GF99', 'SurfaceGF' ] ];
            r += [ Util.stops_to_string( self.deco_info['Stops'] ) ];
        return r;

    def set_cleared_tissue_state(self, deco_model):
        self.tissue_state = deco_model.cleared_tissue_state();

    def set_updated_tissue_state(self, deco_model, prev_point):
        self.tissue_state = deco_model.updated_tissue_state(
            prev_point.tissue_state,
            self.time - prev_point.time,
            Util.depth_to_Pamb(self.depth),
            self.gas );

    def set_updated_deco_info(self, deco_model):
        self.deco_info = deco_model.deco_info(self.tissue_state, self.depth, stateOnly = False);


