import Gas;
from DiveProfile import DiveProfile;

dp = DiveProfile();
dp.append_section(40, 35, gas = Gas.Air());
dp.append_section(30, 20);
dp.append_surfacing();

dp.update_all_tissue_states();
dp.interpolate_points();
# print(dp.dataframe());

