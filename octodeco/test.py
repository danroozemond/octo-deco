# Please see LICENSE.md

import sys, math, time;

from octodeco.deco import Gas, Util, CreateDive, CNSConstants;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();

dp = DiveProfile(gf_low=53, gf_high=53);
dp.append_section(52, 30, gas = Gas.Air());
#dp.add_gas(Gas.Nitrox(50))
dp.add_stops_to_surface();
dp.interpolate_points();
dp.append_section(0.0, 60.0)
dp.update_deco_info();

for x, y in dp.dive_summary().items():
    print('{:25}: {}'.format(x,y));

# simon mitchell's first example, NEDU study, : GF53/53 should give 927.1
# see video 56:39

# Hemmoor planning was 50m, 28 mins, {Nx50, Tx21/30}


#dp.set_gf(35,65, updateStops = True);
# dp.remove_points(lambda x: x.is_interpolated_point, fix_durations = False, update_deco_info = True)
#
# print('With interpolate points, took {:.4f}s'.format(time.perf_counter()-t0));
#
# print(dp.dive_summary());
# for s in dp.runtimetable():
#     print(s);
#
# for p in dp._points:
#     print(p.debug_info());


#sys.exit(0);

for gfs in [(5,75), (35,65), (60,60), (80,55), (200,50), (55,65), (30,90) ]:
    dp = DiveProfile(gf_low = gfs[0], gf_high = gfs[1]);
    dp.append_section(50, 30, gas = Gas.Trimix(21,30));
    dp.add_gas(Gas.Nitrox(50))
    dp.add_stops_to_surface();
    dp.append_section(0.0, 60.0)
    dp.interpolate_points()
    dp.update_deco_info();
    print('GF: {:3d}/{:3d}, deco time: {:5.1f} mins, integral supersat: {:6.1f}'.\
          format(gfs[0], gfs[1], dp.decotime(), dp.integral_supersaturation()));