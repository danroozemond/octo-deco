# Please see LICENSE.md
from . import Util, CNSConstants;


class DivePoint:
    def __init__(self, time, depth, gas, prev):
        self.time = time;
        self.depth = depth;
        self.p_amb = Util.depth_to_Pamb(depth);
        self.gas = gas;
        self.tissue_state = None;
        self.deco_info = None;
        self.is_deco_stop = False;
        self.is_ascent_point = False;
        self.is_interpolated_point = False;
        self.cns_perc = 0.0;
        self.integral_supersat = 0.0;
        self.prev = prev;
        self._gas_consumption_info = dict();
        # NOTE - If you add attributes here, also add migration code to DiveProfileSer
        #

    def __repr__(self):
        return '%.1f:%dm' % (self.time, self.depth);

    @property
    def p_alv(self):
        return self.tissue_state.amb_to_alv(self.p_amb);

    def debug_info(self):
        fmt = '{}{}{} T {:6.1f}  D {:5.1f}  P {:3.1f}={:3.1f}  G {:5s}  DD {:5.1f}  CNS {:5.1f}  FS {:5.1f}  ' +\
               'C {:5.1f}   GF {:5.1f}   SGF {:6.1f}  {}';
        return fmt.format('I' if self.is_interpolated_point else ' ',
                          'D' if self.is_deco_stop else ' ',
                          'A' if self.is_ascent_point else ' ',
                          self.time, self.depth, self.p_amb, self.p_alv, str(self.gas), self.duration,
                          self.cns_perc,
                          self.deco_info['FirstStop'],self.deco_info['Ceil'],
                          self.deco_info['GF99'],
                          self.deco_info['SurfaceGF'],
                          Util.stops_to_string_precise(self.deco_info['Stops']));

    @staticmethod
    def dataframe_columns_deco_info():
        return [ 'FirstStop', 'Ceil', 'Ceil99', 'GF99', 'SurfaceGF', 'LeadingTissueIndex', 'TTS', 'NDL' ];

    @staticmethod
    def dataframe_columns():
        return [ 'time', 'depth', 'gas', 'ppO2', 'CNS' ]  \
                + DivePoint.dataframe_columns_deco_info() \
                + [ 'Stops' ]                             \
                + [ 'IsDecoStop', 'IsAscent', 'IsInterpolated', 'DiveGFLow', 'DiveGFHigh'];

    def repr_for_dataframe(self, diveprofile = None):
        r = [ self.time, self.depth, str(self.gas), self.gas['fO2'] * self.p_amb, self.cns_perc ];
        if self.deco_info is not None:
            r += [ self.deco_info[n] for n in DivePoint.dataframe_columns_deco_info() ];
            r += [ Util.stops_to_string_precise( self.deco_info['Stops'] ) ]
        else:
            r += [ '' for i in range( len(DivePoint.dataframe_columns_deco_info()) + 1) ];
        r += [ 1 if self.is_deco_stop else 0, 1 if self.is_ascent_point else 0, 1 if self.is_interpolated_point else 0];
        r += [ diveprofile.gf_low_profile, diveprofile.gf_high_profile ] if diveprofile is not None else [100, 100];
        return r;

    @property
    def duration(self):
        if self.prev is None:
            return 0.0;
        return self.time - self.prev.time;

    def duration_deco_only(self):
        return self.duration if self.is_deco_stop and self.depth > 0 else 0.0;

    def duration_diving_only(self):
        if self.depth <= 0 and self.prev is not None and self.prev.depth <= 0:
            return 0.0;
        return self.duration;

    def ascent_speed(self):
        d = self.duration;
        if d == 0.0:
            return 0.0;
        assert self.prev is not None;
        return (self.prev.depth - self.depth)/d;

    def set_cleared_tissue_state(self, deco_model):
        self.tissue_state = deco_model.cleared_tissue_state();

    def set_updated_tissue_state(self):
        assert self.time >= self.prev.time;  # Otherwise divepoints are in a broken sequence
        assert self.prev is not None;
        p_amb_section = ( self.p_amb + self.prev.p_amb ) / 2;
        # Tissue state
        self.tissue_state = self.prev.tissue_state.updated_state( self.duration, p_amb_section, self.prev.gas );
        # CNS & integral supersaturation
        pp_o2, _, _ = self.prev.gas.partial_pressures(p_amb_section);
        self.cns_perc = CNSConstants.cns_perc_update(self.prev.cns_perc, p_amb_section, pp_o2, self.duration);
        # Integral supersaturation - approximate with a triangle
        sup_sat_prev = self.prev.tissue_state.abs_supersat(self.prev.p_amb);
        sup_sat_now  = self.tissue_state.abs_supersat(self.p_amb);
        assert sup_sat_prev >= 0.0;
        assert sup_sat_now >= 0.0;
        sup_sat_int_add = self.duration * min(sup_sat_now, sup_sat_prev) \
                          + 0.5 * self.duration * ( max(sup_sat_now, sup_sat_prev) - min(sup_sat_now, sup_sat_prev) );
        self.integral_supersat = self.prev.integral_supersat + sup_sat_int_add;

    def set_updated_deco_info(self, deco_model, gases, amb_to_gf = None ):
        self.deco_info = deco_model.deco_info(self.tissue_state, self.depth, self.gas, gases, amb_to_gf = amb_to_gf );

    def set_updated_gas_consumption_info(self, diveprofile):
        if self.prev is None:
            self._gas_consumption_info = { g : 0.0 for g in diveprofile.gases_carried() };
        else:
            self._gas_consumption_info = self.prev._gas_consumption_info.copy();
        if self.duration > 0 and self.depth > 0:
            rate = diveprofile._gas_consmp_deco if self.is_deco_stop else diveprofile._gas_consmp_bottom;
            gas = self.gas;
            self._gas_consumption_info[ gas ] = self._gas_consumption_info.get(gas, 0.0) \
                                                + self.duration * self.p_amb * rate;

    def gas_consumption_info(self):
        return self._gas_consumption_info;
