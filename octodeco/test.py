# Please see LICENSE.md

import sys
import time

from octodeco.deco import Gas;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();

dp = DiveProfile(gf_low=35, gf_high=85);
# dp.append_section(50, 50, gas = Gas.Trimix(21,35));
dp.append_section(30, 30, gas = Gas.Air());
dp.add_gas(Gas.Nitrox(50))
dp.add_stops_to_surface();
dp.append_section(0,10);
dp.interpolate_points();

print(dp.dive_summary());
for s in dp.runtimetable():
    print(s);

dp.set_gf(55,65);

print(dp.dive_summary());
for s in dp.runtimetable():
    print(s);

t1 = time.perf_counter();
print('Time taken {:.3f}'.format(t1-t0));

sys.exit(0);


for i in range(len(dp._points)):
    p = dp._points[i];
    if 0 < p.time < 130:
        pp = dp._points[i-1];
        # p.set_updated_deco_info(dp.deco_model(), dp._gases_carried, pp.deco_info['amb_to_gf']);
        print('{}{}{} T {:5.1f}  D {:5.1f}  FS {:5.1f}  C {:5.1f}   GF {:4.1f}/{:4.1f}   SGF {:4.1f}  ' \
              .format('I' if p.is_interpolated_point else ' ',\
                      'D' if p.is_deco_stop else ' ',\
                      'A' if p.is_ascent_point else ' ',\
                        p.time, p.depth, p.deco_info['FirstStop'],p.deco_info['Ceil'],
                        p.deco_info['GF99'], p.deco_info['amb_to_gf'](p.p_amb),
                        p.deco_info['SurfaceGF']),
              Util.stops_to_string_precise(p.deco_info['Stops']));

