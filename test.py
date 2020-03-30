# Please see LICENSE.md
import sys;

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

dp = DiveProfile(gf_low = 35, gf_high = 70);
# dp.add_gas( Gas.Air() );
# dp.add_gas( Gas.Nitrox(50) );
dp.append_section(20, 43, Gas.Trimix(21, 35));
# dp.append_surfacing()
# dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
# dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
dp.add_stops_to_surface();
# dp.append_section(0, 30);
# dp.append_surfacing();
dp.interpolate_points();

bm = dp.deco_model();


## TODO BUG ON TRIMIX PROFILE ##
# 45 mins @ 20 meter, Trimix 21/35
# DeepTools: surfacegf @ 35 mins: 93%
#            Dive plan: 1 min @ 9m,   8 min @ 6m,   21 min @ 3m.
# Dan:       surfacegf @ 35 mins: 123%
#            (12.0, 0.0, Tx21/35), (9.0, 6.15234375, Tx21/35), (6.0, 15.732421875, Tx21/35), (3.0, 43.857421875, Tx21/35)
# (bug 2)


# Test
for p in dp.points():
    print('time %.1f, depth %.1f, %s' % ( p.time, p.depth, p.deco_info) );
    if p.time == 44.0:
        print(p.deco_info['Stops']);
        print('stop');
        sys.exit(-1);
