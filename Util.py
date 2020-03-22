def Pamb_to_depth(Pamb):
    return 10.0*(Pamb - 1.0);

def depth_to_Pamb(depth):
    return (depth/10.0) + 1.0;