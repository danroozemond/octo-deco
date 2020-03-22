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

def Air():
    return Gas({ 'fO2': 0.21, 'fN2': 0.79, 'fHe': 0.0 });


def Nitrox(percO2):
    return Gas({ 'fO2': percO2/100, 'fN2':  1 - percO2/100, 'fHe': 0.0 });


def Trimix(percO2, percHe):
    return Gas({'fO2': percO2/100, 'fN2': 1 - percO2/100 - percO2/100, 'fHe': percHe/100});


