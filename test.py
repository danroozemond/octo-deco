# Please see LICENSE.md
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
dp.add_gas( Gas.Air() );
dp.add_gas( Gas.Nitrox(50) );
dp.append_section(20, 35, gas = Gas.Trimix(21, 35));
dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
dp.add_stops_to_surface();
dp.append_section(0, 30);
dp.interpolate_points();


# Test
for p in dp.points():
    # print('time %.1f, depth %.1f, %s' % ( p.time, p.depth, p.deco_info) );
    assert p.deco_info is None or p.deco_info['Ceil'] <= p.depth;

