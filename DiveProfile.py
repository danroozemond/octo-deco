import math;

import pandas as pd;

import Buhlmann;
import Gas;
import Util;

'''
Conventions:
* time is in minutes
* depth is in meters
'''


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
        return [ 'time', 'depth', 'gas', 'ppO2' ] + DivePoint.dataframe_deco_info();

    @staticmethod
    def dataframe_deco_info():
        return [ 'Ceil', 'GF99', 'SurfaceGF', 'Stops' ];

    def repr_for_dataframe(self):
        r = [ self.time, self.depth, str(self.gas), self.gas['fO2'] * Util.depth_to_Pamb(self.depth) ];
        if self.deco_info is not None:
            r += [ self.deco_info[n] for n in DivePoint.dataframe_deco_info() ];
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


class DiveProfile:
    def __init__(self, descent_speed = 20, ascent_speed = 10,
                 deco_model = None, gf_low = 35, gf_high = 70):
        self._points = [ DivePoint(0, 0, Gas.Air()) ];
        self._descent_speed = descent_speed;
        self._ascent_speed = ascent_speed;
        if ( deco_model is not None ):
            self._deco_model = deco_model;
        else:
            self._deco_model = Buhlmann.Buhlmann(gf_low, gf_high);

    def points(self):
        return self._points;

    def dataframe(self):
        return pd.DataFrame([ p.repr_for_dataframe() for p in self._points ],
                            columns = DivePoint.dataframe_columns() );

    def deco_model(self):
        return self._deco_model;

    '''
    Modifying the profile (adding sections etc)
    '''
    def _append_point(self, time_diff, new_depth, gas):
        new_time = self._points[ -1 ].time + time_diff;
        self._points.append(DivePoint(new_time, new_depth, gas));

    def _append_transit(self, new_depth, gas, round_to_mins = True):
        current_depth = self._points[ -1 ].depth;
        depth_diff = current_depth - new_depth;
        transit_time = abs(depth_diff) / self._ascent_speed \
            if depth_diff > 0 \
            else abs(depth_diff) / self._descent_speed;
        transit_time = math.ceil(transit_time) if round_to_mins else transit_time;
        self._append_point(transit_time, new_depth, gas);

    # Relatively clever functions to modify
    def append_section(self, depth, duration, gas = None):
        if gas is None:
            gas = self._points[ -1 ].gas;
        self._append_transit(depth, gas);
        if duration > 0.0:
            self._append_point(duration, depth, gas)

    def append_surfacing(self):
        self.append_section( 0.0, 0 );
        if self._points[ -1 ].gas != Gas.Air():
            self.append_gas_switch( Gas.Air() );

    def append_gas_switch(self, gas, duration = None):
        # Default duration is 0 if still on surface otherwise 1.0
        last_point = self._points[-1];
        if duration is None:
            duration = 1.0 if last_point.depth > 0 else 0.0;
        self._append_point( duration, last_point.depth, gas );

    '''
    Granularity
    '''
    def interpolate_points(self, granularity_mins = 1.0):
        prev_point = None;
        new_points = [];
        for orig_point in self._points:
            # If not the first point: check if we need to interpolate
            # between previous and this, and if so, do
            # We assume previous gas is breathed during interpolated period.
            if prev_point is not None:
                tdiff = orig_point.time - prev_point.time;
                assert tdiff >= 0.0;
                ddiff = orig_point.depth - prev_point.depth;
                tcurr = prev_point.time;
                gas = prev_point.gas if prev_point.depth > 0 else orig_point.gas;
                while tcurr + granularity_mins < orig_point.time:
                    tcurr += granularity_mins;
                    dcurr = prev_point.depth \
                        + (tcurr - prev_point.time) / ( orig_point.time - prev_point.time ) * ddiff;
                    new_points.append(DivePoint(tcurr, dcurr, gas));
            # Finally, add the point itself
            new_points.append(orig_point);
            prev_point = orig_point;
        self._points = new_points;
        self.update_deco_info();

    '''
    Deco model calculations
    '''
    def _update_all_tissue_states(self):
        assert self._points[0].time == 0.0;
        self._points[0].set_cleared_tissue_state( self._deco_model );
        for i in range(1, len(self._points)):
            self._points[i].set_updated_tissue_state( self._deco_model, self._points[i-1]);

    def update_deco_info(self):
        self._update_all_tissue_states();
        for i in range(0, len(self._points)):
            self._points[i].set_updated_deco_info( self._deco_model );
