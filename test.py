import Gas;
from DiveProfile import DiveProfile;

dp = DiveProfile();
dp.append_section(40, 35, gas = Gas.Air());
dp.append_section(30, 20);
dp.append_surfacing();

dp.interpolate_points();
dp.update_deco_info();
print(dp.dataframe());

