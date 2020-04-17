# Please see LICENSE.md
from .DiveProfile import DiveProfile;
from . import Gas;


#
# Create: Demo dive
#
def create_demo_dive():
    dp = DiveProfile(gf_low = 35, gf_high = 70);
    dp.add_gas( Gas.Nitrox(50) );
    dp.append_section(20, 43, Gas.Trimix(21, 35));
    dp.append_section(5, 5, gas = Gas.Trimix(21, 35));
    dp.append_section(40, 35, gas = Gas.Trimix(21, 35));
    dp.add_stops_to_surface();
    dp.append_section(0, 30);
    dp.interpolate_points();
    return dp;


#
# Create: Dive from user input
#
def _ipt_check_depth_time(depth, time):
    try:
        depth = int(depth);
        time = int(time);
        return depth is not None and 0 < depth < 200 \
               and time is not None and 0 < time < 200;
    except:
        return False;

def create_dive_by_depth_time_gas(dtgs, extragas):
    assert len(dtgs) <= 11;
    result = DiveProfile();
    # Parse the dive steps
    cntok = 0;
    for dtg in dtgs:
        gas = Gas.from_string( dtg[2] );
        if gas is not None and _ipt_check_depth_time( dtg[0], dtg[1]):
            result.append_section(int(dtg[0]), int(dtg[1]), gas);
            cntok += 1;
    if cntok == 0:
        return None;
    # Parse any additional gas
    gases = Gas.many_from_string( extragas );
    for g in gases:
        result.add_gas(g);
    # Add deco stops
    result.add_stops_to_surface();
    result.append_section(0, 30);
    result.interpolate_points();
    # Done.
    return result;



#
# Create: Dive from CSV
#
#TODO
