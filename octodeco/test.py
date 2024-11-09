# Please see LICENSE.md
import sys, math, time;

from octodeco.deco import Gas, Util, CreateDive, CNSConstants;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();

# simon mitchell's first example, NEDU study, : GF53/53 should give 927.1
# see video 56:39

# dp = DiveProfile(gf_low=53, gf_high=53);
# dp.append_section(50, 30, gas = Gas.Trimix(21, 35));
# dp.add_gas(Gas.Nitrox(50))
# dp.add_gas(Gas.Nitrox(80))
# dp.add_stops_to_surface();
# dp.interpolate_points();
# dp.append_section(0.0, 30.0)
# dp.update_deco_info();

# dp = DiveProfile(gf_low=53, gf_high=53);
# dp.append_section(51.8, 30, gas = Gas.Air());
# dp.add_stops_to_surface();
# dp.interpolate_points();
# dp.append_section(0.0, 30.0)
# dp.update_deco_info();
#
#
# for x, y in dp.dive_summary().items():
#     print('{:25}: {}'.format(x,y));
# print('====')
#
# dt = dp.decotime();
# dp0 = dp.clean_copy();
#
# for i in range(1,18):
#     gf_low = 5*i;
#     gf_high = dp0.find_gf_high(gf_low, dt);
#     assert gf_high is not None;
#     cp = dp0.clean_copy();
#     cp.remove_surface_at_end();
#     cp.set_gf(gf_low, gf_high, updateStops = True);
#     is1 = cp.integral_supersaturation_at_end();
#     cp.append_section(0, 10);
#     cp.update_deco_info();
#     is2 = cp.integral_supersaturation_at_end();
#     cp.append_section(0, 20);
#     cp.update_deco_info();
#     is3 = cp.integral_supersaturation_at_end();
#     print(f'{gf_low:5}/{gf_high:5} -> deco time: {cp.decotime():5.1f} mins, int. supersat: 0min: {is1:6.1f}, 10min: {is2:6.1f}, 30min: {is3:6.6f}');
#
#
# sys.exit(0);


# Simon mitchell's third example,
# RT=70, GF 50/54 gives 342.2
# RT=58, GF 30/85 gives 480.8
# 50 meters, 25 mins, on 18/45,
# decompression on 50% and O2
#
# My implementation gives 112.6 on 30/85
# and 85.3 on 50/54
# now 342.2/480.8=0.71; 85.3/112.6=0.76 (so comparable)

#dp = DiveProfile(gf_low=50, gf_high=54,last_stop_depth = 3);
dp = DiveProfile(gf_low=30, gf_high=85,last_stop_depth = 6);
dp.append_section(50, 22.5, gas = Gas.Trimix(18,45));
dp.add_gas(Gas.Nitrox(50))
dp.add_gas(Gas.Nitrox(99))
dp.add_stops_to_surface();
dp.append_section(0.0, 30.0)
dp.interpolate_points();
dp.update_deco_info();

for x, y in dp.dive_summary().items():
    print('{:25}: {}'.format(x,y));
print('====')

for p in dp._points:
    print(p.debug_info());

