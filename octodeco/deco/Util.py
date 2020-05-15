# Please see LICENSE.md
import math;


def Pamb_to_depth(Pamb):
    d = 10.0*(Pamb - 1.0);
    return round(d, 1);


def depth_to_Pamb(depth):
    return (depth/10.0) + 1.0;


def Pamb_to_Pamb_stop(p_amb, direction = 'down'):
    t = Pamb_to_depth(p_amb);
    if (t % 3) > 0.01:
        if direction == 'down':
            t = 3*(math.floor(t/3) + 1);
        elif direction == 'up':
            t = 3 * (math.ceil(t / 3) - 1);
    return depth_to_Pamb(t);


def next_stop_Pamb(p_amb):
    return p_amb - 0.3;


def stops_to_string(stops):
    return ' '.join([ '%i@%im' % ( round(s[1]), s[0] ) for s in stops if round(s[1]) >= 1 ]);


def stops_to_string_precise(stops):
    return ' '.join([ '%.1f@%im[%s]' % ( s[1], s[0], s[2] ) for s in stops ]);
