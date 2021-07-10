import sys, math, time, os;

from octodeco.deco import Gas, Util, CreateDive, CNSConstants;
from octodeco.deco.DiveProfile import DiveProfile;

ANALYSIS_PATH=os.getenv('ANALYSIS_PATH');
print(os.path.basename(ANALYSIS_PATH))

SOURCE_XML = os.path.join(ANALYSIS_PATH,'20210705.export.xml');
