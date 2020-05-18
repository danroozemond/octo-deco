# Please see LICENSE.md
import csv;

from . import Gas;
from .DiveProfile import DiveProfile;


#
# Create: Demo dive
#
def create_demo_dive():
    dp = DiveProfile(gf_low = 35, gf_high = 70);
    dp.is_demo_dive = True;
    dp.add_gas(Gas.Nitrox(50));
    dp.append_section(20, 45, Gas.Trimix(21, 35));
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
        return depth is not None and 0 < depth < 200 and time is not None and 0 < time < 200;
    except:
        return False;


def create_dive_by_depth_time_gas(dtgs, extragas):
    assert len(dtgs) <= 11;
    result = DiveProfile();
    # Parse the dive steps
    cntok = 0;
    for dtg in dtgs:
        gas = Gas.from_string(dtg[ 2 ]);
        if gas is not None and _ipt_check_depth_time(dtg[ 0 ], dtg[ 1 ]):
            result.append_section(int(dtg[ 0 ]), int(dtg[ 1 ]), gas, correct_duration_with_transit = True);
            cntok += 1;
    if cntok == 0:
        return None;
    # Parse any additional gas
    gases = Gas.many_from_string(extragas);
    for g in gases:
        result.add_gas(g);
    # Add deco stops
    result.add_stops_to_surface();
    result.append_section(0, 10);
    result.interpolate_points();
    # Done.
    return result;


#
# Create: Dive from CSV
#
class ParseError(Exception):
    """to raise & catch unexpected CSV format"""
    pass


class QNDCache:
    def __init__(self, fun):
        self.lastargs = None;
        self.lastres = None;
        self.fun = fun;

    def __call__(self, *args):
        # Returns False, None if same as last time
        # Returns True, f(ipt) if new
        if args != self.lastargs:
            self.lastargs = args;
            self.lastres = self.fun(args);
            return True, self.lastres;
        else:
            return False, self.lastres;


def create_from_shearwater_csv(lines):
    # First two lines contain details about settings etc
    hlines = lines[ 0:2 ];
    reader = csv.DictReader(hlines);
    row = reader.__next__();
    try:
        gf_low = int(row[ 'GF Minimum' ]);
        gf_high = int(row[ 'GF Maximum' ]);
        divenr = int(row[ 'Dive Number' ]);
    except KeyError as err:
        raise ParseError('Could not parse header row (%s)' % err.args);
    result = DiveProfile(gf_low = gf_low, gf_high = gf_high);
    result.add_custom_desc = 'SW-%i' % int(divenr);
    # Rest is actually the dive
    # (Using DictReader is probably not the most efficient, but soit)
    del lines[ 0:2 ];
    reader = csv.DictReader(lines);
    gas = Gas.Air();
    cc = QNDCache( lambda p : Gas.Trimix(100.0*p[0], 100.0*p[1]));
    for row in reader:
        # Extract info
        try:
            t = float(row[ 'Time (ms)' ]) / 6e4;
            d = float(row[ 'Depth' ]);
            fo2 = float(row[ 'Fraction O2' ]);
            fhe = float(row[ 'Fraction He' ]);
        except KeyError as err:
            raise ParseError('Could not parse dive point (%s)' % err.args);
        # Gas
        if d > 0.0:
            nw, gas = cc(fo2, fhe);
            if nw:
                result.add_gas(gas);
        # Point
        result._append_point_abstime(t, d, gas);
    # Wrap up
    result.update_deco_info();
    result.update_deco_model_info(result.deco_model(), update_profile = True);
    return result;


def create_from_octodeco_csv(lines):
    result = None;
    reader = csv.DictReader(lines);
    gas = Gas.Air();
    cc = QNDCache( lambda args : Gas.from_string(args[0]));
    for row in reader:
        # Extract info
        try:
            t = float(row[ 'time' ]);
            d = float(row[ 'depth' ]);
            g = str(row['gas']);
            ids = ( int(row['IsDecoStop']) == 1 );
            iip = ( int(row['IsInterpolated']) == 1 );
            iap = ( int(row.get('IsAscent',0)) == 1 );
            if result is None:
                dgflow = int(row[ 'DiveGFLow' ]);
                dgfhigh = int(row[ 'DiveGFHigh' ]);
        except KeyError as err:
            raise ParseError('Could not parse dive point (%s)' % err.args);
        # First line:
        if result is None:
            result = DiveProfile( gf_low = dgflow, gf_high = dgfhigh );
        # Gas
        if d > 0.0:
            nw, gas = cc(g);
            if nw:
                result.add_gas(gas);
        # Point
        p = result._append_point_abstime(t, d, gas);
        p.is_deco_stop = ids;
        p.is_ascent_point = iap;
        p.is_interpolated_point = iip;
    # Wrap up
    result.add_custom_desc = 'CSV';
    result.update_deco_info();
    result.update_deco_model_info( result.deco_model(), update_profile = True );
    return result;


def create_from_csv_file(filename, func):
    lines = [ ];
    for line in open(filename, 'r'):
        lines.append(line);
    return func(lines);
