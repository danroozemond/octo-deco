# Please see LICENSE.md

from deco import Gas, Util, CreateDive;
from deco.DiveProfile import DiveProfile;

# dp = DiveProfile();
# dp.append_section(40, 35, gas = Gas.Air());
# dp.append_section(30, 20);
# dp.append_surfacing();
# dp.add_stops();
# dp.interpolate_points();
# dp.update_deco_info();
# print(dp.dataframe());

dp = CreateDive.create_from_shearwater_csv_file("C:/Users/Dan Roozemond/Desktop/30189285#219_2020-01-05.csv");
print(dp.description());

for p in dp._points:
    print(p.time, p.depth, p.deco_info['SurfaceGF'])
