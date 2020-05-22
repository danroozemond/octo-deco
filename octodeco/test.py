# Please see LICENSE.md

import sys, math, time;

from octodeco.deco import Gas, Util, CreateDive;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();

dp = DiveProfile(gf_low=35, gf_high=65);
dp.append_section(30, 35, gas = Gas.Air());
dp.add_gas(Gas.Nitrox(50))
dp.add_stops_to_surface();

# dp.set_gf(0,0, updateStops = False);
dp.remove_points(lambda x: x.is_interpolated_point, fix_durations = False, update_deco_info = True)

print(dp.dive_summary());
for s in dp.runtimetable():
    print(s);

for i in range(len(dp._points)):
    p = dp._points[i];
    if 36 < p.time < 46:
        pp = dp._points[i-1];
        # p.set_updated_deco_info(dp.deco_model(), dp._gases_carried, pp.deco_info['amb_to_gf']);
        print('{}{}{} T {:6.1f}  D {:5.1f}  G {:5s}  DD {:5.1f}  FS {:5.1f}  C {:5.1f}   GF {:5.1f}/{:4.1f}   SGF {:6.1f}  ' \
              .format('I' if p.is_interpolated_point else ' ',\
                      'D' if p.is_deco_stop else ' ',\
                      'A' if p.is_ascent_point else ' ',\
                        p.time, p.depth, str(p.gas), p.duration(), p.deco_info['FirstStop'],p.deco_info['Ceil'],
                        p.deco_info['GF99'], p.deco_info['amb_to_gf'](p.p_amb),
                        p.deco_info['SurfaceGF']),
              Util.stops_to_string_precise(p.deco_info['Stops']));

