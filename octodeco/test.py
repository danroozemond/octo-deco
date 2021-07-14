# Please see LICENSE.md

import sys, math, time;

from octodeco.deco import Gas, Util, CreateDive, CNSConstants;
from octodeco.deco.DiveProfile import DiveProfile;

t0 = time.perf_counter();



dp = DiveProfile(gf_low=55, gf_high=70);
dp.append_section(52, 10-52/20, gas = Gas.Air());
dp.append_section(48, 20-4/20, gas = Gas.Air());
dp.add_gas(Gas.Nitrox(50))
dp.add_gas(Gas.Nitrox(80))
dp.add_stops_to_surface();
dp.append_section(0.0, 10.0)
dp.interpolate_points();
dp.update_deco_info();

for x, y in dp.dive_summary().items():
    print('{:25}: {}'.format(x,y));

for s in dp.runtimetable():
    print('{:3.0f} {:7.1f}   {:10}'.format(s['depth'],s.get('time',0.0),str(s.get('gas',''))))

