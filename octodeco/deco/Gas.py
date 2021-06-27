# Please see LICENSE.md

import re;

"""
Gases are represented as simple dicts mapping string to float
 key: (fO2, fN2, fHe)
"""

class Gas(dict):
    def __init__(self,*args,**kwargs) :
        dict.__init__(self,*args,**kwargs);

    def __repr__(self):
        if self[ 'fHe' ] == 0:
            if self[ 'fO2' ] == 0.21:
                return "Air";
            else:
                return "Nx%d" % (100 * self[ 'fO2' ]);
        else:
            return 'Tx%d/%d' % (100 * self[ 'fO2' ], 100 * self[ 'fHe' ]);

    def __hash__(self):
        return hash( self['fO2'] ) + 3 * hash(self['fHe']);

    def __eq__(self, other):
        if self is None or other is None:
            return self is None and other is None;
        elif hasattr(self, 'cython_array') and hasattr(other, 'cython_array'):
            return self.cython_array == other.cython_array;
        else:
            return all([ self[g] == other[g] for g in [ 'fO2', 'fN2', 'fHe' ]]);

    def __ne__(self, other):
        return not self.__eq__(other);


def Air():
    return Gas({ 'fO2': 0.21, 'fN2': 0.79, 'fHe': 0.0 });


def Nitrox(percO2):
    return Gas({ 'fO2': percO2/100, 'fN2':  1 - percO2/100, 'fHe': 0.0 });


def Trimix(percO2, percHe):
    return Gas({'fO2': percO2/100, 'fN2': 1 - percO2/100 - percHe/100, 'fHe': percHe/100});


def from_string(s):
    if s is None:
        return None;
    s = s.strip().lower();
    m = re.match('(?i)(air|nx[0-9][0-9]|tx[0-9][0-9]/[0-9][0-9])', s )
    if m is None:
        return None;
    # Ok, at this point we know it's reasonably safe to parse.
    # If you're reading this and you disagree, let me know :)
    result = None;
    if s == 'air':
        result = Air();
    elif s.startswith('nx'):
        result = Nitrox(int(s[2:4]));
    elif s.startswith('tx'):
        result = Trimix(int(s[2:4]), int(s[5:7]));
    return result;


def many_from_string(s):
    r = [ from_string(ss) for ss in s.split(',') ];
    r = [ g for g in r if g is not None ];
    return r;


def best_gas(gases, p_amb, max_pO2):
    # What is the best deco gas at this ambient pressure?
    suitable = [ gas for gas in gases if p_amb * gas[ 'fO2' ] <= max_pO2 ];
    if len(suitable) == 0:
        suitable = gases;
    gas = max(suitable, key = lambda g: ( g[ 'fO2' ], g['fHe'] ) );
    return gas;
