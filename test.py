from DiveProfile import DiveProfile;
import Buhlmann, Gas;

dp = DiveProfile();
dp.append_section(40, 25);
dp.append_section(30, 10);
dp.append_surfacing();

# print(dp.dataframe());

