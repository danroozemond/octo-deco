import math;

import pandas as pd;

import Buhlmann;
import Gas;

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

    def __repr__(self):
        return '%.1f:%dm' % (self.time, self.depth);

    def repr_for_dataframe(self):
        return [ self.time, self.depth, str(self.gas) ];

    @staticmethod
    def dataframe_columns():
        return [ 'time', 'depth', 'gas' ]

    def set_cleared_tissue_state(self, deco_model):
        self.tissue_state = deco_model.cleared_tissue_state();

    def set_updated_tissue_state(self, deco_model, prev_point):
        self.tissue_state = deco_model.updated_tissue_state(
            prev_point.tissue_state,
            self.time - prev_point.time,
            self.depth,
            self.gas );


class DiveProfile:
    def __init__(self, descent_speed = 20, ascent_speed = 10, deco_model = Buhlmann.Buhlmann()):
        self._points = [ DivePoint(0, 0, Gas.Air()) ];
        self._descent_speed = descent_speed;
        self._ascent_speed = ascent_speed;
        self._deco_model = deco_model;

    def points(self):
        return self._points;

    def dataframe(self):
        return pd.DataFrame([ p.repr_for_dataframe() for p in self._points ],
                            columns = DivePoint.dataframe_columns() );

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

    def append_surfacing(self, gas = None):
        self.append_section( 0.0, 0 );

    '''
    Granularity
    '''
    # TODO

    '''
    Deco model calculations
    '''
    def update_all_tissue_states(self):
        assert self._points[0].time == 0.0;
        self._points[0].set_cleared_tissue_state( self._deco_model );
        for i in range(1, len(self._points)):
            self._points[i].set_updated_tissue_state( self._deco_model, self._points[i-1]);
