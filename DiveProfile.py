import math;
import time;

import pandas as pd;

import Buhlmann;
import Gas;
# import Util;
from DivePoint import DivePoint

'''
Conventions:
* time is in minutes
* depth is in meters
'''


class DiveProfile:
    def __init__(self, descent_speed = 20, ascent_speed = 10,
                 deco_model = None, gf_low = 35, gf_high = 70):
        self._points = [ DivePoint(0, 0, Gas.Air(), None) ];
        self._descent_speed = descent_speed;
        self._ascent_speed = ascent_speed;
        self._gases_carried = set();
        self._deco_stops_computation_time = 0.0;
        self._desc_deco_model_display = '';
        self._desc_deco_model_profile = '';
        if deco_model is not None:
            self._deco_model = deco_model;
        else:
            self._deco_model = Buhlmann.Buhlmann(gf_low, gf_high, self._descent_speed, self._ascent_speed);

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
        v = {'Deco model (display)': self._desc_deco_model_display,
             'Deco model (profile)': self._desc_deco_model_profile,
             'Gases carried': self._gases_carried
             };

        divetime = sum([ p.duration() for p in self._points if p.depth > 0 ]);
        decotime = sum([ p.duration() for p in self._points if p.depth > 0 and p.is_deco_stop ]);

        v['Total dive time'] = '%.1f mins' % divetime;
        v['Decompression time'] = '%.1f mins' % decotime;
        v['Deco profile comp time'] = '%.1f secs' % self._deco_stops_computation_time;
        return v;

    '''
    Modifying the profile (adding sections etc)
    '''
    def add_gas(self, gas):
        self._gases_carried.add( gas );

    def _append_point(self, time_diff, new_depth, gas):
        new_time = self._points[ -1 ].time + time_diff;
        p = DivePoint(new_time, new_depth, gas, self._points[-1]);
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
    def append_section(self, depth, duration, gas = None, transit = True):
        if gas is None:
            gas = self._points[ -1 ].gas;
        if depth > 0:
            self.add_gas(gas);
        if transit:
            self._append_transit(depth, gas);
        if duration > 0.0:
            self._append_point(duration, depth, gas)

    def append_surfacing(self, transit = True):
        self.append_section( 0.0, 0.1, transit = transit );
        if self._points[ -1 ].gas != Gas.Air():
            self.append_gas_switch( Gas.Air() );

    def append_gas_switch(self, gas, duration = None):
        # Default duration is 0 if still on surface otherwise 1.0
        last_point = self._points[-1];
        if duration is None:
            duration = 1.0 if last_point.depth > 0 else 0.0;
        if last_point.depth > 0:
            self.add_gas(gas);
        self._append_point( duration, last_point.depth, gas );

    def add_stops_to_surface(self):
        self.append_surfacing( transit = False );
        self.add_stops();

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
                    pt = DivePoint(tcurr, dcurr, gas, new_points[-1]);
                    new_points.append(pt);
                    pt.is_deco_stop = orig_point.is_deco_stop;
                    pt.is_interpolated_point = True;
            # Finally, add the point itself
            orig_point.prev = new_points[-1] if len(new_points) > 0 else None;
            new_points.append(orig_point);
            prev_point = orig_point;
        self._points = new_points;
        self.update_deco_info();

    def uninterpolate_points(self):
        self._points = [ p for p in self._points if not p.is_interpolated_point ];

    '''
    Deco model info
    '''
    def _update_all_tissue_states(self):
        assert self._points[0].time == 0.0;
        self._points[0].set_cleared_tissue_state( self._deco_model );
        for i in range(1, len(self._points)):
            self._points[i].set_updated_tissue_state( self._deco_model );

    def update_deco_info(self):
        self._update_all_tissue_states();
        amb_to_gf = None;
        for p in self._points:
            p.set_updated_deco_info( self._deco_model, self._gases_carried, amb_to_gf = amb_to_gf );
            amb_to_gf = p.deco_info['amb_to_gf'];
        self._desc_deco_model_profile = self._deco_model.description();

    '''
    Deco profile creation
    '''
    def add_stops(self):
        t0 = time.perf_counter();
        deco_model = self.deco_model();
        assert self._points[0].time == 0.0;
        old_points = self._points;
        self._points = [ old_points[0] ];
        self._points[0].set_cleared_tissue_state( deco_model );
        amb_to_gf = None;
        i = 1;
        while i < len(old_points):
            op = old_points[i];
            p = self._append_point( op.duration(), op.depth, op.gas );
            # Update tissues, based on last point considered
            p.set_updated_tissue_state( deco_model );
            p.set_updated_deco_info( deco_model, self._gases_carried, amb_to_gf = amb_to_gf );
            # print('existing point; time %.1f prev time %.1f duration %.1f depth: %.1f ceil: %.1f stops: %s' \
            #       % ( p.time, p.prev.time, p.duration(), p.depth, \
            #           p.deco_info['Ceil'], Util.stops_to_string(p.deco_info['Stops']) ) );
            amb_to_gf = p.deco_info['amb_to_gf'];
            gf_now = amb_to_gf(p.p_amb);
            # print('add_stops, time %.1f, depth %.1f, GF %.1f ?<=? %.1f' \
            #       % ( p.time, p.depth, p.deco_info['GF99'], gf_now) );
            # Are we in violation?
            if p.deco_info['GF99'] > gf_now:
                # Undo adding this point, then attempt to readd in next iteration
                self._points.pop();
                # Add points before, but take care to live along the GF line
                stops, p_ceiling, amb_to_gf = deco_model.compute_deco_profile(
                                            self._points[-1].tissue_state,
                                            self._points[-1].p_amb,
                                            self._gases_carried,
                                            p_target = op.p_amb,
                                            amb_to_gf = amb_to_gf );
                assert len(stops) > 0;
                # print("  adding stops:", Util.stops_to_string(stops));
                # print("  based stops on point:", self._points[-1].deco_info)
                # print("  computed ceiling: %.1f = %.1f" %( p_ceiling, Util.Pamb_to_depth(p_ceiling) ));
                # Do not forget to update tissue state and deco info
                for s in stops:
                    np = len(self._points);
                    self.append_section( s[0], s[1], gas = s[2] );
                    # print('updating tissue state and deco info, array lengths:', np, len(self._points))
                    # Update tissue state and deco info
                    for j in range(np, len(self._points)):
                        p = self._points[ j ]
                        p.is_deco_stop = True;
                        p.set_updated_tissue_state(deco_model);
                        p.set_updated_deco_info(deco_model, self._gases_carried, amb_to_gf = amb_to_gf);
            else:
                # Add new point (tissue state etc is computed correctly by construction)
                i += 1;
        # Done!
        self._desc_deco_model_profile = deco_model.description();
        self._desc_deco_model_display = deco_model.description();
        self._deco_stops_computation_time = time.perf_counter() - t0;

    '''
    Modifying dive
    '''
    def set_gf( self, gf_low, gf_high ):
        self._deco_model = Buhlmann.Buhlmann(gf_low, gf_high, self._descent_speed, self._ascent_speed);
        self.update_deco_info();

    def update_stops( self ):
        self._points = [ p for p in self._points if not p.is_deco_stop ];
        self.uninterpolate_points();
        self.add_stops();
        self.interpolate_points();




