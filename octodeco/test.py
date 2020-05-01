# Please see LICENSE.md
import time, sys;
import copy;
import pandas as pd;

from octodeco.deco import CreateDive, Gas;
from octodeco.deco.DiveProfile import DiveProfile;

# for db in [False,True]:
#     dp = CreateDive.create_demo_dive(debugBuhlmann = db);
#     times = list();
#     s = dp.deco_model().TissueState;
#     for i in range(5):
#         t0 = time.perf_counter();
#         dp.set_gf(35, 70, updateStops = True);
#         t1 = time.perf_counter();
#         # print('{:2} {} #points:   {}'.format(i, s, len(dp.points())));
#         print('{:2} {} time:      {:.3f}'.format(i, s, t1 - t0));
#         times.append(t1-t0);
#     print('{} avg: {:.3f}s'.format( s, sum(times)/len(times)));


dp = DiveProfile(gf_low=35, gf_high=70);
dp.append_section(30, 20, gas = Gas.Trimix(21,35));
dp.append_section(5, 5, gas = Gas.Air());
dp.append_section(50, 30, gas = Gas.Trimix(15,40));
dp.add_gas(Gas.Nitrox(50));
dp.add_gas(Gas.Nitrox(99));
dp.add_stops_to_surface();
dp.append_section(0,10);
t0 = time.perf_counter();
dp.interpolate_points();
print('For interpolate_points ({} points): {:.3f}\n'.format(len(dp._points), time.perf_counter()-t0));

for k,v in dp.dive_summary().items():
    print(k,':',v);

print("\n");
dp2 = copy.deepcopy(dp);
dp2.set_gf(20,50, updateStops = True);
dp.update_deco_info();
for k,v in dp.dive_summary().items():
    print(k,':',v);

t0 = time.perf_counter();
res = dp.decotimes_for_gfs();
t1 = time.perf_counter();
df = pd.DataFrame(res).transpose();
print(df);
print('Total computation time: {:.3f}s'.format(t1-t0))
print(df.to_html(classes="smalltable", header="true", escape=False))
# --> format the elements by linking to /dive/show/..?gflow=..&gfhigh=..


# for i in range(len(dp._points)):
#     p = dp._points[i];
#     if 107 < p.time < 130:
#         pp = dp._points[i-1];
#         # p.set_updated_deco_info(dp.deco_model(), dp._gases_carried, pp.deco_info['amb_to_gf']);
#         print('{}{} T {:5.1f}  D {:5.1f}  FS {:5.1f}  C {:5.1f}   GF {:4.1f}/{:4.1f}   SGF {:4.1f}  ' \
#               .format('I' if p.is_interpolated_point else ' ',\
#                       'D' if p.is_deco_stop else ' ',\
#                         p.time, p.depth, p.deco_info['FirstStop'],p.deco_info['Ceil'],
#                         p.deco_info['GF99'], p.deco_info['amb_to_gf'](p.p_amb),
#                         p.deco_info['SurfaceGF']),
#               Util.stops_to_string_precise(p.deco_info['Stops']));

