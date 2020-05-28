# Please see LICENSE.md

from . import Util;

# Constants: map ppO2 to %(CNS build-up per minute)
CNS_PER_MIN = \
[ (0.60,0.14), (0.64,0.15), (0.68,0.17), (0.70,0.18), (0.72,0.18), (0.76,0.20), (0.80,0.22), (0.84,0.24), (0.86,0.25), \
(0.88,0.26), (0.90,0.28), (0.92,0.29), (0.94,0.30), (0.96,0.31), (0.98,0.32), (1.00,0.33), (1.02,0.35), (1.04,0.36), \
(1.06,0.38), (1.08,0.40), (1.10,0.42), (1.15,0.44), (1.16,0.45), (1.18,0.46), (1.20,0.48), (1.22,0.49), (1.24,0.51), \
(1.26,0.52), (1.28,0.54), (1.30,0.56), (1.32,0.57), (1.34,0.60), (1.36,0.62), (1.38,0.64), (1.39,0.65), (1.40,0.67), \
(1.41,0.68), (1.42,0.69), (1.43,0.71), (1.44,0.72), (1.45,0.74), (1.46,0.76), (1.47,0.78), (1.48,0.79), (1.49,0.81), \
(1.50,0.83), (1.51,0.89), (1.52,0.95), (1.53,1.03), (1.54,1.11), (1.55,1.21), (1.56,1.33), (1.57,1.48), (1.58,1.67), \
(1.59,1.90), (1.60,2.22), (1.65,3.40), (1.70,5.80), (1.75,8.70), (1.80,10.20), (1.85,14.50), (1.90,19.50), \
(1.95,26.60), (2.00,100.00) ];
CNS_HALFTIME_SURFACE = 90;  # 90 minutes
PP_SURFACE = Util.SURFACE_PRESSURE * 0.21;


def _cns_perc_update_surface(cns_perc_before, duration):
    return cns_perc_before * 0.5 ** ( duration / CNS_HALFTIME_SURFACE );


def _cns_per_min(pp_o2):
    # Binary search (taking care of the boundaries a bit more precisely)
    i0 = 0;
    i1 = len(CNS_PER_MIN)-1;
    if CNS_PER_MIN[i0][0] > pp_o2:
        # Linearly interpolate between surface and this
        # 0.21 < pp_o2 < pp_min (=0.60)
        pp_surf = PP_SURFACE;
        pp_min, cpm_min = CNS_PER_MIN[0];
        f = max(0.0, ( pp_o2 - pp_surf ) / ( pp_min - pp_surf ));
        return f * cpm_min;
    if CNS_PER_MIN[i1][0] < pp_o2:
        # Just return max value
        return CNS_PER_MIN[i1][1];
    while i1-i0 > 1:
        h = i0 + int((i1-i0)/2);
        pp_h = CNS_PER_MIN[h][0];
        if pp_h < pp_o2:
            i0 = h;
        else:
            i1 = h;
    if h > 0 and CNS_PER_MIN[h-1][0] == pp_o2:
        h -= 1;
    if h < len(CNS_PER_MIN) - 1 and CNS_PER_MIN[h][0] < pp_o2:
        h += 1;
    return CNS_PER_MIN[h][1];


def cns_perc_update(cns_perc_before, p_amb, pp_o2, duration):
    if p_amb < Util.SURFACE_PRESSURE:
        # Update using halftime
        return _cns_perc_update_surface( cns_perc_before, duration );
    else:
        # Linearly interpolate between 0 and this
        return cns_perc_before + duration * _cns_per_min(pp_o2)


