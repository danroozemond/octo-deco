# Please see LICENSE.md

import sys, math, time;

from octodeco.deco import Gas, Util, CreateDive;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();

dp = DiveProfile(gf_low=75, gf_high=85);
dp.append_section(30, 18, gas = Gas.Nitrox(32));
dp.add_gas(Gas.Nitrox(50))
dp.add_stops_to_surface();
dp.interpolate_points()

dp.set_gf(35,65, updateStops = True);
dp.remove_points(lambda x: x.is_interpolated_point, fix_durations = False, update_deco_info = True)

print(dp.dive_summary());
for s in dp.runtimetable():
    print(s);

for p in dp._points:
    print(p.debug_info());
