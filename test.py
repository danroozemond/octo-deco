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
dp.append_section(20, 43, Gas.Air()); #Gas.Trimix(21, 35));
# dp.append_surfacing()
# dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
# dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
# dp.add_stops_to_surface();
# dp.append_section(0, 30);
# dp.append_surfacing();
dp.interpolate_points();

bm = dp.deco_model();


## TODO ##
# 45 mins @ 20 meter, with Air, after 35 mins:
#   the surface gf matches DeepTools (87%)
# Ceil says 0.0, should be ~5.9 (bug 1)
# same profile, but Trimix 21/35
# DeepTools: surfacegf deeptools: 93%,
#            Dive plan: 1 min @ 9m,   8 min @ 6m,   21 min @ 3m.
# Dan: 30 min @ 6m, 38 min @ 3m
# (bug 2)
# (To check after fixing bug 1)


# Test
for p in dp.points():
    print('time %.1f, depth %.1f, %s' % ( p.time, p.depth, p.deco_info) );
    if p.time == 35:
        print('stop');
        sys.exit(-1)


