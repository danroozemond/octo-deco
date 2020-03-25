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
    Deco model info
    '''
    def dive_summary(self):
        v = { 'Decompression model': self._deco_model.description() };

        divetime = sum([ self._points[i].time - self._points[i-1].time for i in range(1, len(self._points))
                         if self._points[i].depth > 0]);
        decotime = sum([ self._points[i].time - self._points[i-1].time for i in range(1, len(self._points))
                         if self._points[i].depth > 0 and self._points[i].is_deco_stop]);

        v['Total dive time'] = '%.1f mins'% divetime;
        v['Decompression time'] = '%.1f mins'% decotime;
        return v;

    '''
    Modifying the profile (adding sections etc)
    '''
    def _append_point(self, time_diff, new_depth, gas):
        new_time = self._points[ -1 ].time + time_diff;
        p = DivePoint(new_time, new_depth, gas);
        self._points.append(p);
        return p;

    def _append_transit(self, new_depth, gas, round_to_mins = False):
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
                    pt = DivePoint(tcurr, dcurr, gas);
                    new_points.append(pt);
                    pt.is_deco_stop = orig_point.is_deco_stop;
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
        amb_to_gf = None;
        for i in range(0, len(self._points)):
            p = self._points[i];
            gf_now = None if amb_to_gf is None else amb_to_gf( Util.depth_to_Pamb( p.depth ) );
            p.set_updated_deco_info( self._deco_model, amb_to_gf = amb_to_gf );
            if amb_to_gf is None and p.is_deco_stop:
                amb_to_gf = p.deco_info.get('amb_to_gf');

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
        amb_to_gf = None;
        i = 1;
        while i < len(old_points):
            op = old_points[i];
            p = self._append_point( op.time - old_points[i-1].time, op.depth, op.gas );
            print('appending existing point time/depth = %s/%s' % (op.time - old_points[i-1].time, op.depth ));
            # Update tissues, based on last point considered
            p.set_updated_tissue_state( deco_model, self._points[-2]);
            p.set_updated_deco_info( deco_model, amb_to_gf = amb_to_gf );
            gf_now = p.deco_info['amb_to_gf'](Util.depth_to_Pamb(p.depth));
            print('  point:', p.time, p.depth, 'ceils', p.deco_info['Ceil'], p.deco_info['Ceil99'], 'gf now', gf_now);
            # Are we in violation?
            if p.deco_info['GF99'] > gf_now:
                # Undo adding this point, then attempt to readd in next iteration
                self._points.pop();
                # Add points before, but take care to live along the
                stops, p_ceiling, amb_to_gf = deco_model.compute_deco_profile(
                                            self._points[-1].tissue_state,
                                            Util.depth_to_Pamb( self._points[-1].depth ),
                                            p_target = Util.depth_to_Pamb(op.depth),
                                            amb_to_gf = amb_to_gf );
                print('  adding stops:', 'ceil', p_ceiling, 'stops',stops);
                assert len(stops) > 0;
                # Do not forget to update tissue state and deco info
                for s in stops:
                    np = len(self._points);
                    self.append_section( s[0], s[1], gas = s[2]);
                    print('    appended section %s %s %s' % s)
                    # Update tissue state and deco info
                    for j in range(np, len(self._points)):
                        self._points[j].is_deco_stop = True;
                        self._points[j].set_updated_tissue_state(deco_model, self._points[ j - 1 ]);
                        self._points[j].set_updated_deco_info(deco_model, amb_to_gf = amb_to_gf);
            else:
                # Add new point (tissue state etc is computed correctly by construction)
                print('  No further action required');
                i += 1;
