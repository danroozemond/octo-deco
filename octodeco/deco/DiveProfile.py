# Please see LICENSE.md
import copy;
import datetime
import math;
import time;
from typing import Set, Any

import pandas as pd;
import pytz;

from . import Buhlmann;
from . import DiveProfileSer;
from . import Gas;
from . import Cylinder;
from .DivePoint import DivePoint;

'''
Conventions:
* time is in minutes
* depth is in meters
'''


class DiveProfile:
    _gases_carried: Set[ Any ]

    def __init__(self,
                 descent_speed = 20, ascent_speed = 10,
                 max_pO2_deco = 1.60, gas_switch_mins = 3.0,
                 last_stop_depth = 3,
                 gas_consmp_bottom = 20.0, gas_consmp_deco = 20.0,
                 gf_low = 35, gf_high = 70):
        self._points = [ DivePoint(0, 0, Gas.Air(), None) ];
        self._descent_speed = descent_speed;
        self._ascent_speed = ascent_speed;
        self._max_pO2_deco = max_pO2_deco;
        self._gas_switch_mins = gas_switch_mins;
        self._last_stop_depth = last_stop_depth;
        self._gas_consmp_bottom = gas_consmp_bottom;
        self._gas_consmp_deco = gas_consmp_deco;
        self._gas_consmp_emerg_factor = 4.0;
        self._gas_consmp_emerg_mins = 4.0;
        self._gases_carried = set();
        self._cylinders_used = None;
        self._deco_stops_computation_time = 0.0;
        self._full_info_computation_time = 0.0;
        self._desc_deco_model_display = '';
        self.gf_low_display = gf_low;
        self.gf_high_display = gf_high;
        self._desc_deco_model_profile = '';
        self.gf_low_profile = gf_low;
        self.gf_high_profile = gf_high;
        self.created = datetime.datetime.now(tz = pytz.timezone('Europe/Amsterdam'));
        self.add_custom_desc = None;
        self.custom_desc = None;
        self.is_demo_dive = False;
        self.is_ephemeral = False;
        self.is_public = True;
        self.db_version = DiveProfileSer.CURRENT_VERSION;

        # NOTE - If you add attributes here, also add migration code to DiveProfileSer
        #
        self.update_deco_model_info( self.deco_model(gf_low, gf_high), update_display = True);

    def points(self):
        return self._points;

    def full_copy(self):
        cp = copy.deepcopy(self);
        if hasattr(cp, 'dive_id'):
            delattr(cp, 'dive_id')
        if hasattr(cp, 'user_id'):
            delattr(cp, 'user_id');
        return cp;

    def clean_copy(self):
        cp = self.full_copy();
        cp._remove_all_extra_points( update_deco_info = False );
        return cp;

    def dataframe(self):
        return pd.DataFrame([ p.repr_for_dataframe(diveprofile = self)
                              for p in self._points ],
                            columns = DivePoint.dataframe_columns());

    def deco_model(self, gf_low = None, gf_high = None):
        gf_low = gf_low if gf_low is not None else self.gf_low_display;
        gf_high = gf_high if gf_high is not None else self.gf_high_display;
        dm = Buhlmann.Buhlmann(gf_low, gf_high,
                               self._descent_speed, self._ascent_speed,
                               self._max_pO2_deco, self._gas_switch_mins,
                               self._last_stop_depth);
        return dm;

    '''
    Dive / deco model info
    '''
    def dive_summary(self):
        v = {'Deco model (display)': self._desc_deco_model_display,
             'Deco model (profile)': self._desc_deco_model_profile,
             'Gases carried': {str(g) for g in self._gases_carried},
             'Last stop': f'{self._last_stop_depth} m',
             'Total dive time': f'{self.divetime():.1f} mins',
             'Decompression time': f'{self.decotime():.1f} mins',
             'CNS max': f'{self.cns_max():.1f}%',
             'Integral supersaturation (at end)': f'{self.integral_supersaturation_at_end():.1f} bar*mins',
             'Integral supersaturation (at surfacing)': f'{self.integral_supersaturation_at_surfacing():.1f} bar*mins',
             'Deco profile comp time': f'{self._deco_stops_computation_time:.2f} secs',
             'Full info comp time': f'{self._full_info_computation_time:.2f} secs'
             };

        return v;

    def decotime(self):
        return sum(map(lambda p: p.duration_deco_only(), self._points));

    def divetime(self):
        return sum(map(lambda p: p.duration_diving_only(), self._points));

    def cns_max(self):
        return max(map(lambda p: p.cns_perc, self._points));

    def max_depth(self):
        return max(map(lambda p: p.depth, self._points));

    def integral_supersaturation_at_end(self):
        return self._points[-1].integral_supersat;

    def integral_supersaturation_at_surfacing(self):
        i = self._find_idx_of_surfacing_point();
        return self._points[i].integral_supersat;

    def description(self):
        if self.custom_desc is not None:
            return self.custom_desc;

        maxdepth = self.max_depth();
        dtc = self.created.strftime('%d-%b-%Y %H:%M');
        r = f'{maxdepth:.1f} m / {self.divetime():.0f} mins ({dtc})';
        if self.add_custom_desc is not None and self.add_custom_desc != '':
            r = f'{self.add_custom_desc}: {r}';
        return r;

    def update_deco_model_info(self, deco_model, update_display = False, update_profile = False):
        if update_display:
            self._desc_deco_model_display = deco_model.description();
            self.gf_low_display = deco_model.gf_low;
            self.gf_high_display = deco_model.gf_high;
        if update_profile:
            self._desc_deco_model_profile = deco_model.description();
            self.gf_low_profile = deco_model.gf_low;
            self.gf_high_profile = deco_model.gf_high;

    '''
    Modifying the profile (adding sections etc)
    '''
    def add_gas(self, gas):
        self._gases_carried.add( gas );

    def gases_carried(self):
        return self._gases_carried;

    def _append_point_abstime(self, new_time, new_depth, gas):
        if len(self._points) == 1:
            self._points[0].gas = gas;
        p = DivePoint(new_time, new_depth, gas, self._points[-1]);
        self._points.append(p);
        p.set_updated_gas_consumption_info(self);
        return p;

    def _append_point(self, time_diff, new_depth, gas):
        new_time = self._points[ -1 ].time + time_diff;
        return self._append_point_abstime(new_time, new_depth, gas);

    def _append_point_fix_ascent(self, op):
        # Returns new point, and whether or not one was added
        have_point_added = False;
        time_needed = ( self._points[-1].depth - op.depth ) / self._ascent_speed;
        if time_needed > op.duration:
            # Add deco point
            transit_point_duration = time_needed - op.duration;
            transit_point_depth = self._points[-1].depth - self._ascent_speed*transit_point_duration;
            tp = self._append_point( transit_point_duration, transit_point_depth, self._points[-1].gas );
            tp.is_ascent_point = True;
            have_point_added = True;
        # Add the original point
        p = self._append_point(op.duration, op.depth, op.gas);
        return p, have_point_added;

    def _append_transit(self, new_depth, gas, round_to_mins = False):
        current_depth = self._points[ -1 ].depth;
        depth_diff = current_depth - new_depth;
        transit_time = abs(depth_diff) / self._ascent_speed \
            if depth_diff > 0 \
            else abs(depth_diff) / self._descent_speed;
        transit_time = math.ceil(transit_time) if round_to_mins else transit_time;
        self._append_point(transit_time, new_depth, gas);
        return transit_time;

    # Relatively clever functions to modify
    def append_section(self, depth, duration, gas = None, transit = True, correct_duration_with_transit = False):
        if gas is None:
            if depth == 0:
                gas = Gas.Air();
            else:
                gas = self._points[ -1 ].gas;
        if depth > 0:
            self.add_gas(gas);
        if transit:
            transit_time = self._append_transit(depth, gas);
            if correct_duration_with_transit:
                duration -= transit_time;
        if duration > 0.0:
            self._append_point(duration, depth, gas)

    def append_surfacing(self, transit = True):
        self.append_section( 0.0, 0.1, transit = transit );
        if self._points[ -1 ].gas != Gas.Air():
            self.append_gas_switch( Gas.Air() );
        # Round to nearest integral minute, just cause it looks nice
        p = self._points[-1];
        if int(p.time) != p.time:
            self._append_point_abstime( math.ceil(p.time), p.depth, p.gas);

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
                    pt.is_ascent_point = orig_point.is_ascent_point;
                    pt.is_interpolated_point = True;
            # Finally, add the point itself (remove duplicates)
            orig_point.prev = new_points[-1] if len(new_points) > 0 else None;
            if orig_point.prev is None \
                or orig_point.time != orig_point.prev.time or orig_point.depth != orig_point.prev.depth \
                or ( orig_point.prev.is_deco_stop or orig_point.prev.is_ascent_point or orig_point.prev.is_interpolated_point
                     and not ( orig_point.is_deco_stop or orig_point.is_ascent_point or orig_point.is_interpolated_point)):
                new_points.append(orig_point);
                prev_point = orig_point;
        self._points = new_points;
        self.update_deco_info();

    '''
    Generating a runtime
    '''
    def _runtimetable_gas_usage_info(self, p_amb, gas, cyls, gas_used):
        liters = gas_used[gas];
        cyl = cyls[gas];
        r = { gas: { 'liters_used': liters,
                     'bars_used' : cyl.liters_to_bars(liters),
                     'perc_used' : cyl.liters_used_to_perc(liters),
                     'cyl_name' : cyl.name } };
        return r;

    def runtimetable(self):
        # Collect the interesting points: last points of each section
        points = [];
        for i in range(len(self._points)-1):
            p = self._points[i];
            np = self._points[i+1];
            if p.is_interpolated_point or p.is_ascent_point or p.depth == 0.0:
                continue;
            if p.depth == np.depth and p.gas != np.gas:
                # This is a gas switch stop
                continue;
            if p.depth != np.depth or p.gas != np.gas:
                points.append(p)
            # When importing CSV's, this doesn't make sense
            if len(points) > 30:
                return None;
        # Transform to runtime
        res = []; lastgas = points[0].gas;
        cyls = self.cylinders_used();
        for p in points:
            gci = p.gas_consumption_info();
            r = {'depth':p.depth,
                 'time':p.time};
            if p.gas != lastgas or len(res) == 0:
                r[ 'gas' ] = p.gas;
                r[ 'gas_usage' ] = self._runtimetable_gas_usage_info(p.p_amb, lastgas, cyls, gci);
                lastgas = p.gas;
            else:
                r[ 'gas_usage' ] = self._runtimetable_gas_usage_info(p.p_amb, p.gas, cyls, gci);
            res.append(r);
        res.append({'depth': 0.0});
        return res;

    '''
    Deco model info
    '''
    def _update_all_tissue_states(self):
        assert self._points[0].time == 0.0;
        self._points[0].set_cleared_tissue_state( self.deco_model() );
        for i in range(1, len(self._points)):
            self._points[i].set_updated_tissue_state( );

    def update_deco_info(self):
        t0 = time.perf_counter();
        deco_model = self.deco_model();
        self._update_all_tissue_states();
        amb_to_gf = None;
        for p in self._points:
            p.set_updated_deco_info( deco_model, self._gases_carried, amb_to_gf = amb_to_gf );
            amb_to_gf = p.deco_info['amb_to_gf'];
            p.set_updated_gas_consumption_info(self);
        self.update_deco_model_info(deco_model, update_display = True)
        self._full_info_computation_time = time.perf_counter() - t0;

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
        self._points[0].set_updated_deco_info(deco_model, self._gases_carried);
        amb_to_gf = None;
        i = 1;
        while i < len(old_points):
            op = old_points[i];
            oldlen = len(self._points);
            # Potentially prepend extra point to cover ascent speed; append original point
            p, extra_added = self._append_point_fix_ascent( op );
            # Update tissues, based on last point considered
            for j in range(oldlen, len(self._points)):
                self._points[j].set_updated_tissue_state( );
                self._points[j].set_updated_deco_info( deco_model, self._gases_carried, amb_to_gf = amb_to_gf );
                amb_to_gf = self._points[j].deco_info['amb_to_gf'];
            # Are we in violation?
            if p.tissue_state.max_over_supersat(amb_to_gf, p.p_amb) > 0.01:
                # Add points before, but take care to live along the GF line
                before_stop = self._points[-2] if not extra_added else self._points[-3];
                stops, p_ceiling, amb_to_gf = deco_model.compute_deco_profile(
                                            before_stop.tissue_state,
                                            before_stop.p_amb,
                                            before_stop.gas,
                                            self._gases_carried,
                                            p_target = op.p_amb,
                                            add_gas_switch_time = True,
                                            amb_to_gf = amb_to_gf );
                if len(stops) == 0:
                    # Exceptional case, we were /right/ on the edge
                    i += 1;
                    continue;
                # Undo adding this point, then attempt to readd in next iteration
                self._points.pop();
                if extra_added:
                    self._points.pop();
                # Do not forget to update tissue state and deco info
                for s in stops:
                    np = len(self._points);
                    self.append_section( s[0], s[1], gas = s[2] );
                    # Update tissue state and deco info
                    for j in range(np, len(self._points)):
                        p = self._points[ j ]
                        p.is_deco_stop = True;
                        p.set_updated_tissue_state();
                        p.set_updated_deco_info(deco_model, self._gases_carried, amb_to_gf = amb_to_gf);
                        # assert p.depth >= p.deco_info['Ceil']-0.1;
            else:
                # Add new point (tissue state etc is computed correctly by construction)
                # Careful, there's another i += 1 in an exceptional case above.
                i += 1;
        # Done!
        self.update_deco_model_info(deco_model, update_display = True, update_profile = True)
        self._deco_stops_computation_time = time.perf_counter() - t0;

    '''
    Modifying dive
    '''
    def set_gf( self, gf_low, gf_high, updateStops = False ):
        self.gf_low_display = gf_low;
        self.gf_high_display = gf_high;
        if updateStops:
            self.update_stops();
        else:
            self.update_deco_info();

    def _find_idx_of_surfacing_point(self):
        i = len(self._points)-1;
        while i > 1 and self._points[i-1].depth == 0:
            i -= 1;
        return i;

    def length_of_surface_section(self):
        endtime = self._points[ -1 ].time;
        begintime = self._points[self._find_idx_of_surfacing_point()].time;
        return round(endtime-begintime);

    def remove_surface_at_end(self):
        # Removes surface section at end, returns amt of time removed
        endtime = self._points[-1].time;
        i = self._find_idx_of_surfacing_point();
        begintime = self._points[i].time;
        del self._points[i+1:];
        return endtime-begintime;

    def remove_points(self, remove_filter, fix_durations, update_deco_info = True):
        new_points = [];
        removed_duration = 0.0;
        for p in self._points:
            d = p.duration;
            if remove_filter(p):
                removed_duration += d;
            else:
                p.prev = new_points[-1] if len(new_points) > 0 else None;
                new_points.append(p);
                if fix_durations:
                    p.duration_to_remove = removed_duration;
        self._points = new_points;
        if fix_durations:
            for p in self._points:
                p.time -= p.duration_to_remove;
                del p.duration_to_remove;
        if update_deco_info:
            self.update_deco_info();

    def _remove_all_extra_points(self, update_deco_info = True):
        self.remove_points(lambda x: x.is_interpolated_point, fix_durations = False, update_deco_info = False)
        self.remove_points(lambda x: x.is_ascent_point, fix_durations = True, update_deco_info = False)
        self.remove_points(lambda x: x.is_deco_stop, fix_durations = True, update_deco_info = False)
        if update_deco_info:
            self.update_deco_info();

    def update_stops( self, interpolate = True, actually_add_stops = True ):
        # Remove surface time
        surfacetime = self.remove_surface_at_end();
        # Remove deco stops & interpolated points
        self._remove_all_extra_points( update_deco_info = False );
        # Bring back stops, surface section
        self.append_surfacing(transit = False);
        if actually_add_stops:
            self.add_stops();
        self.append_section(0, surfacetime);
        # interpolated points
        if interpolate:
            self.interpolate_points();


    '''
    Evaluating various GF's and impact on deco time
    '''
    def decotime_for_gf(self, gf_low, gf_high):
        cp = self.clean_copy();
        cp.gf_low_display = gf_low;
        cp.gf_high_display = gf_high;
        cp.add_stops_to_surface();
        return cp.decotime();

    def decotimes_for_gfs(self, gflows = None, gfhighs = None):
        if gfhighs is None:
            gfhighs = [ 45, 65, 70, 75, 85, 95 ]
        if gflows is None:
            gflows = [ 25, 35, 45, 55 ]
        rtt = self.runtimetable();
        if rtt is None:
            # We could not create a runtime table, because it did not make sense
            # => also gfdecotable does not make sense
            return None;
        # Prepare template
        cp = self.clean_copy();
        # Do the math
        res = dict();
        for gflow in gflows:
            res[gflow] = dict();
            for gfhigh in gfhighs:
                res[ gflow ][ gfhigh ] = cp.decotime_for_gf( gflow, gfhigh );
        return res;

    def find_gf_high(self, given_gf_low, target_deco_time):
        cp = self.clean_copy();
        def vdt(x):
            return cp.decotime_for_gf(given_gf_low, x);
        a = 5;
        b = 120;
        if vdt(a) < target_deco_time or vdt(b) > target_deco_time:
            # The lowerbound is too short or the upperbound is too long -> abort
            return None;
        n = 0;
        while b > a + 1:
            # Anti-infinite loop
            n += 1; assert n < 100;
            # The real search
            h = int(a + (b-a)/2);
            if vdt(h) > target_deco_time:
                a = h;
            else:
                b = h;
        # Not entirely nice, but necessary evil given we only have integral GFs
        da = abs(vdt(a) - target_deco_time);
        db = abs(vdt(b) - target_deco_time);
        return a if da < db else b;


    '''
    Gas consumption computations
    '''
    def gas_consumption(self):
        return self._points[-1].gas_consumption_info();

    @staticmethod
    def _gas_consumption_ok(perc, emergency):
        thr1 = 100.0*2/3 if not emergency else 95.0;
        thr2 = 90.0      if not emergency else 99.0;
        ok = 'good' if perc < thr1 else \
            ('warn' if perc < thr2 else 'bad');
        return ok;

    def _gas_consumption_info(self, emergency):
        cyls = self.cylinders_used();
        gci = self.gas_consumption();
        gci_more = { gas : {
                'liters': liters,
                'bars': cyls[gas].liters_to_bars(liters),
                'perc': cyls[gas].liters_used_to_perc(liters),
                'cyl_name': cyls[gas].name,
                'ok' : self._gas_consumption_ok(cyls[gas].liters_used_to_perc(liters), emergency)
            }
            for gas,liters in gci.items() } ;
        return { 'decotime' : self.decotime(), 'gas_consmp': gci_more };

    def _update_profile_lost_gases(self, lost_gases, interpolate = True):
        self._gases_carried.difference_update(set(lost_gases));
        for i in range(len(self._points)):
            p = self._points[i];
            if p.gas not in self._gases_carried and p.depth > 0:
                # The gas is considered to be breathed from this point to the next, so pO2 should be
                # OK for both.
                p_amb = max(p.p_amb, self._points[i+1].p_amb) if i < len(self._points) - 1 \
                    else p.p_amb;
                p.gas = Gas.best_gas( self._gases_carried, p_amb, self._max_pO2_deco );
        self.update_stops( interpolate = interpolate );

    def copy_profile_lost_gases(self, lost_gases, interpolate = True):
        cp = self.clean_copy();
        cp.custom_desc = self.description() + ' - lost {}'.format(lost_gases);
        cp._update_profile_lost_gases(lost_gases, interpolate = interpolate);
        return cp;

    def gas_consumption_analysis(self):
        # First, everything as planned
        gci = self._gas_consumption_info(False);
        r = [ { 'lost': None, 'emergency' : self.analyze_emergency_gas_need(), **gci} ];
        # Identify bottom gas / deco gas
        bottom_gas = self._guess_bottom_gas();
        deco_gases = self.gases_carried().copy();
        deco_gases.remove(bottom_gas);
        # Then, for each deco gas ..
        cp = self.clean_copy()
        for gas in deco_gases:
            ccp = cp.copy_profile_lost_gases([gas], interpolate = False);
            gci = ccp._gas_consumption_info(True);
            r.append({'lost': str(gas),
                      'emergency' : ccp.analyze_emergency_gas_need(),
                      **gci});
        return r;

    def analyze_emergency_gas_need(self):
        bottom_gas = self._guess_bottom_gas();
        cyl = self.cylinders_used()[bottom_gas];
        liters_used_bottom_gas = self.gas_consumption()[bottom_gas];
        max_p_amb = max(map(lambda p: p.p_amb, self._points));
        liters_needed_emerg = 2 * 2 * 4 * self._gas_consmp_bottom * max_p_amb;
        perc_emerg = cyl.liters_used_to_perc(liters_used_bottom_gas + liters_needed_emerg);
        ok = self._gas_consumption_ok(perc_emerg, True);
        r = { 'bottom_gas' : bottom_gas,
              'cyl_name' : cyl.name,
              'perc_used' : cyl.liters_used_to_perc(liters_used_bottom_gas),
              'perc_emerg' : perc_emerg,
              'ok' : ok };
        return r;


    '''
    Gas consumption: cylinders
    '''
    def _guess_bottom_gas(self):
        gc = self.gas_consumption();
        bottom_gas = max(gc, key = lambda k: gc[ k ]);
        return bottom_gas;

    def _guess_cylinders(self):
        bottom_gas = self._guess_bottom_gas();
        r = { k : Cylinder.Cylinder('D12', 24, 200) if k == bottom_gas else Cylinder.Guess(v, k)
              for k,v in self.gas_consumption().items() };
        return r;

    def cylinders_used(self):
        if self._cylinders_used is None:
            self._cylinders_used = self._guess_cylinders();
        return self._cylinders_used;

