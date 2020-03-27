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
# TODO comment this back in
# dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
# dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
dp.append_surfacing();
dp.add_stops( );
# dp.add_stops_to_surface();  # TODO test this
# dp.append_section(0, 30);
dp.interpolate_points();


# Test
for p in dp.points():
    print('time %.1f, depth %.1f, %s' % ( p.time, p.depth, p.deco_info) );
    assert p.deco_info is None or p.deco_info['Ceil'] <= p.depth;

# To debug this: explicitly call deco_info on that tissue_state, with that amb_to_gf,  and add debug info in Buhlmann
# .. check why p_ceiling is not quite right in that case
# .. and next to checking p_amb_tol - p_amb_next_stop, also check the GF's after that certain time