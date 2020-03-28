import math;


def Pamb_to_depth(Pamb):
    d = 10.0*(Pamb - 1.0);
    return round(d, 1);


def depth_to_Pamb(depth):
    return (depth/10.0) + 1.0;


def Pamb_to_Pamb_stop(p_amb):
    t = Pamb_to_depth(p_amb);
    if (t % 3) > 0.01:
        t = 3*(math.floor(t/3) + 1);
    return depth_to_Pamb(t);


def next_stop_Pamb(p_amb):
    return p_amb - 0.3;


def stops_to_string(stops):
    return ' '.join([ '%.1f@%im' % ( round(s[1]), s[0] ) for s in stops if s[1] >= 1 ]);
