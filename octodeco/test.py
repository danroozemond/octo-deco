# Please see LICENSE.md

import sys, math, time;

from octodeco.deco import Gas, Util, CreateDive, CNSConstants;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();

dp = DiveProfile(gf_low=35, gf_high=70,
                 gas_consmp_bottom = 16,
                 gas_consmp_deco = 14);
dp.append_section(52, 10, gas = Gas.Trimix(21,35));
dp.append_section(48, 20, gas = Gas.Trimix(21,35));
dp.add_gas(Gas.Nitrox(50))
dp.add_gas(Gas.Nitrox(80))
dp.add_stops_to_surface();
dp.interpolate_points()
dp.append_section(0.0, 10.0)

#dp.set_gf(35,65, updateStops = True);
#dp.remove_points(lambda x: x.is_interpolated_point, fix_durations = False, update_deco_info = True)
#print('With interpolate points, took {:.4f}s'.format(time.perf_counter()-t0));

print(dp.dive_summary());
for s in dp.runtimetable():
    print(s);

print(dp.gas_consumption())

# for p in dp._points:
#     print(p.debug_info());
#     print('pt',p._gas_consumption_info);
