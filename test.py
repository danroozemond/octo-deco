import Gas;
from DiveProfile import DiveProfile;

# dp = DiveProfile();
# dp.append_section(40, 35, gas = Gas.Air());
# dp.append_section(30, 20);
# dp.append_surfacing();
# dp.add_stops();
# dp.interpolate_points();
# dp.update_deco_info();
# print(dp.dataframe());

dp = DiveProfile();
# dp.add_gas( Gas.Nitrox(50));
dp.append_section(20, 35, gas = Gas.Trimix(21, 35));
dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
dp.append_surfacing();
#dp.interpolate_points();
dp.add_stops();
dp.append_section(0, 30);
dp.interpolate_points();
