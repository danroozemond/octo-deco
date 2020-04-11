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

def Air():
    return Gas({ 'fO2': 0.21, 'fN2': 0.79, 'fHe': 0.0 });


def Nitrox(percO2):
    return Gas({ 'fO2': percO2/100, 'fN2':  1 - percO2/100, 'fHe': 0.0 });


def Trimix(percO2, percHe):
    return Gas({'fO2': percO2/100, 'fN2': 1 - percO2/100 - percHe/100, 'fHe': percHe/100});


def from_string(s):
    if s is None:
        return None;
    m = re.match('(?i)(air|nx[0-9][0-9]|tx[0-9][0-9]/[0-9][0-9])', s )
    if m is None:
        return None;
    # Ok, at this point we know it's reasonably safe to parse.
    # If you're reading this and you disagree, let me know :)
    s = s.lower();
    result = None;
    if s == 'air':
        result = Air();
    elif s.startswith('nx'):
        result = Nitrox(int(s[2:4]));
    elif s.startswith('tx'):
        result = Trimix(int(s[2:4]), int(s[5:7]));
    return result;
