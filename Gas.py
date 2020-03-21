"""
Gases are represented as simple dicts mapping string to float
 key: fO2, fN2, fHe)
"""

def Air():
    return { 'fO2': 0.21, 'fN2': 0.79, 'fHe': 0.0 };


def Nitrox(percO2):
    return { 'fO2': percO2/100, 'fN2':  1 - percO2/100, 'fHe': 0.0 };


def Trimix(percO2, percHe):
    return {'fO2': percO2/100, 'fN2': 1 - percO2/100 - percO2/100, 'fHe': percHe/100};


def gas_to_str(d):
    if d['fHe'] == 0:
        if d['fO2'] == 0.21:
            return "Air";
        else:
            return "Nx%d" % (100*d['fO2']);
    else:
        return 'Tx%d/%d' % ( 100*d['fO2'], 100*d['fHe']);
