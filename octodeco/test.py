# Please see LICENSE.md

from octodeco.deco import Gas, Util, CreateDive;
from octodeco.deco.DiveProfile import DiveProfile;

dp = DiveProfile();
dp.append_section(50, 50, gas = Gas.Trimix(11,40));
dp.append_section(30, 50, gas = Gas.Trimix(21,35));
dp.add_gas(Gas.Nitrox(50));
dp.add_gas(Gas.Nitrox(99));
dp.add_stops_to_surface();
dp.interpolate_points();

for p in dp._points:
    if p.time >= 50 and p.time <= 60:
        print(p.time, p.depth, p.is_deco_stop, p.is_interpolated_point, p.deco_info['SurfaceGF'])

dp.set_gf(60,100);
dp.update_stops();
print('\nwith 60/100');
for p in dp._points:
    if p.time >= 50 and p.time <= 60:
        print(p.time, p.depth, p.deco_info['SurfaceGF'])
