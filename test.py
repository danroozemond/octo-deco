# Please see LICENSE.md

from deco import Gas, Util;
from deco.DiveProfile import DiveProfile;

# dp = DiveProfile();
# dp.append_section(40, 35, gas = Gas.Air());
# dp.append_section(30, 20);
# dp.append_surfacing();
# dp.add_stops();
# dp.interpolate_points();
# dp.update_deco_info();
# print(dp.dataframe());

dp = DiveProfile(gf_low = 70, gf_high = 70);
# dp.add_gas( Gas.Air() );
dp.add_gas( Gas.Nitrox(50) );
# dp.append_section(20, 43, Gas.Trimix(21, 35));
# dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
# dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
dp.append_section(50,20, gas = Gas.Trimix(21,35));
dp.add_stops_to_surface();
dp.update_deco_info()
# dp.append_section(0, 30);
# dp.append_surfacing();
# )

bm = dp.deco_model();

for i in range(1,len(dp._points)):
    p = dp._points[i];
    if p.time > 20 and p.time < 30:
        print('%.1f' % p.time, p.depth, p.gas, 'st', Util.stops_to_string(p.deco_info['Stops']), 'info', p.deco_info);

dp.interpolate_points();
print('After interpolate:');
for i in range(1,len(dp._points)):
    p = dp._points[i];
    if p.time > 20 and p.time < 30:
        print('%.1f' % p.time, p.depth, p.gas, 'st', Util.stops_to_string(p.deco_info['Stops']), 'info', p.deco_info);

# # Test
# for p in dp.points():
#     print('time %.1f, depth %.1f, %s' % ( p.time, p.depth, p.deco_info) );
#     print('fs: %.1f, ceil: %.1f / %.1f'% ( p.deco_info['FirstStop'], p.deco_info['Ceil'], bm.p_ceiling_for_amb_to_gf(p.tissue_state, p.deco_info['amb_to_gf'])));
#     if p.time >= 35.0:
#         print('stop');
#         sys.exit(-1);
