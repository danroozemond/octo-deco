# Please see LICENSE.md
import math;

# Surface pressure of 1.0132 bar.

# Water pressure: EN13319: 1020 kg/m^3.
# Pressure measured in Pa = N/m^3 ; 1 bar = 10^5 Pa.
# 1020 kg/m^3 = 1020*9.8 N/m^3 = 9996 N/m^3 = 0.09996 bar
# So 10 meters of water (at EN13319) is 0.9996 bar

# Google tells us:
# 10 m salt/sea water = 1.00693064 bar
# 10 m fresh water    = 0.980638 bar
# So that seems to work out just about right.

SURFACE_PRESSURE = 1.0132; #bar
BAR_PER_METER = 1020*9.80*1e-5;
METER_PER_BAR = 1/BAR_PER_METER;


def Pamb_to_depth(Pamb):
    d = METER_PER_BAR*( Pamb - SURFACE_PRESSURE );
    return round(d, 1);


def depth_to_Pamb(depth):
    return (depth * BAR_PER_METER) + SURFACE_PRESSURE;


def Pamb_to_Pamb_stop(p_amb, direction = 'down'):
    t = Pamb_to_depth(p_amb);
    if (t % 3) > 0.01:
        if direction == 'down':
            t = 3*(math.floor(t/3) + 1);
        elif direction == 'up':
            t = 3 * (math.ceil(t / 3) - 1);
    return depth_to_Pamb(t);


def next_stop_Pamb(p_amb):
    return p_amb - 3*BAR_PER_METER;


def stops_to_string(stops):
    return ' '.join([ '%i@%im' % ( round(s[1]), s[0] ) for s in stops if round(s[1]) >= 1 ]);


def stops_to_string_precise(stops):
    return ' '.join([ '%.1f@%im[%s]' % ( s[1], s[0], s[2] ) for s in stops ]);
