import math;


def Pamb_to_depth(Pamb, round_to=0.1):
    d = 10.0*(Pamb - 1.0);
    if round_to == 0.0:
        return d;
    if d < 0:
        return 0;
    d_rounded = round_to * math.ceil( d / round_to );
    return d_rounded;

def depth_to_Pamb(depth):
    return (depth/10.0) + 1.0;