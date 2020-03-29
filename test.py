# Please see LICENSE.md
import Gas;
from DiveProfile import DiveProfile;

import sys;

# dp = DiveProfile();
# dp.append_section(40, 35, gas = Gas.Air());
# dp.append_section(30, 20);
# dp.append_surfacing();
# dp.add_stops();
# dp.interpolate_points();
# dp.update_deco_info();
# print(dp.dataframe());

dp = DiveProfile(gf_low = 99, gf_high = 99);
# dp.add_gas( Gas.Air() );
# dp.add_gas( Gas.Nitrox(50) );
dp.append_section(20, 45, gas = Gas.Air()); # Gas.Trimix(21, 35));
dp.append_surfacing()
# dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
# dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
dp.add_stops_to_surface();
# dp.append_section(0, 30);
# dp.append_surfacing();
# dp.interpolate_points();


# Test
for p in dp.points():
    print('time %.1f, depth %.1f, %s' % ( p.time, p.depth, p.deco_info) );
    if ( round(10*p.time) == 96 ):
        print('\n\n\nThis is strange: ceil is 8.2 but stops gives 3.0?');
        p.set_updated_deco_info(dp.deco_model(), dp._gases_carried, p.deco_info['amb_to_gf'])
        print('time %.1f, depth %.1f, %s' % (p.time, p.depth, p.deco_info));
        print('\n\ntodo - still way too conservative compare to eg. DeelTools. Example dive 35@20, 35@40, '
              'at 3m, 50mins vs 30mins')
# Klopt niet - hij krijgt een stop (van 4 min) voor z'n kiezen.
        sys.exit(-1);


