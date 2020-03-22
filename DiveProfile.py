import math;
import pandas as pd;
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

    def __repr__(self):
        return '%.1f:%dm' % (self.time, self.depth);

    def repr_for_dataframe(self):
        return [ self.time, self.depth, str(self.gas) ];

    @staticmethod
    def dataframe_columns():
        return [ 'time', 'depth', 'gas' ]


class DiveProfile:
    def __init__(self, descent_speed = 20, ascent_speed = 10):
        self._points = [ DivePoint(0, 0, Gas.Air()) ];
        self._descent_speed = descent_speed;
        self._ascent_speed = ascent_speed;

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
