import math;

import pandas as pd;

import Buhlmann;
import Gas;
import Util;
from DivePoint import DivePoint

'''
Conventions:
* time is in minutes
* depth is in meters
'''


class DiveProfile:
    def __init__(self, descent_speed = 20, ascent_speed = 10,
                 deco_model = None, gf_low = 35, gf_high = 70):
        self._points = [ DivePoint(0, 0, Gas.Air()) ];
        self._descent_speed = descent_speed;
        self._ascent_speed = ascent_speed;
        if deco_model is not None:
            self._deco_model = deco_model;
        else:
            self._deco_model = Buhlmann.Buhlmann(gf_low, gf_high);

    def points(self):
        return self._points;

    def dataframe(self):
        return pd.DataFrame([ p.repr_for_dataframe() for p in self._points ],
                            columns = DivePoint.dataframe_columns());

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
    Deco model info
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

    '''
    Deco profile creation
    '''
    def add_stops(self):
        # TODO Add interpolate here?
        deco_model = self.deco_model();
        assert self._points[0].time == 0.0;
        old_points = self._points;
        self._points = [ old_points[0] ];
        self._points[0].set_cleared_tissue_state( deco_model );
        time_shift = 0;
        i = 1;
        while i < len(old_points):
            p = old_points[i];
            # Update tissues, based on last point considered
            p.set_updated_tissue_state( deco_model, self._points[-1]);
            p.set_updated_deco_info( deco_model );
            print(p.time, p.depth, p.deco_info['Ceil']);
            if p.depth < p.deco_info['Ceil']:
                # Add points before, then do not increase i because we recheck
                stops = deco_model.compute_deco_profile(self._points[-1].tissue_state, Util.depth_to_Pamb(p.depth));
                # Do not forget to update tissue state and deco info
                print("Recomputed stops:");
                print(Util.stops_to_string(stops));

                i += 100;  # No increment
            else:
                # Add new point (tissue state etc is computed correctly by construction)
                p.time += time_shift;
                self._points.append(p);
                i += 1;
