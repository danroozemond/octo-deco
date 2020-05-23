# Please see LICENSE.md

import sys, math, time;

from octodeco.deco import Gas, Util, CreateDive;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();

dp = DiveProfile(gf_low=5, gf_high=65);
dp.append_section(50, 50.5, gas = Gas.Air());
dp.add_gas(Gas.Nitrox(50))
dp.add_stops_to_surface();
dp.interpolate_points()

# dp.set_gf(0,0, updateStops = False);
dp.remove_points(lambda x: x.is_interpolated_point, fix_durations = False, update_deco_info = True)

print(dp.dive_summary());
for s in dp.runtimetable():
    print(s);

for p in dp._points:
    print(p.debug_info());
