import Gas;
from DiveProfile import DiveProfile;

dp = DiveProfile();
dp.append_section(40, 25, gas = Gas.Air());
dp.append_section(30, 10);
dp.append_surfacing();

dp.update_all_tissue_states();

print(dp.dataframe());

