import sys, math, time, os, re;
import xml.etree.ElementTree as ET

from octodeco.deco import Gas, Util, CreateDive, CNSConstants;
from octodeco.deco.DiveProfile import DiveProfile;

##
## Loading the data from XML
##

ANALYSIS_PATH = os.getenv('ANALYSIS_PATH');
SOURCE_XML = os.path.join(ANALYSIS_PATH,'20210705.export.xml');

tree = ET.parse(SOURCE_XML);
root = tree.getroot();

def get_xml_dive(dive_number):
    matches = root.findall("./dives/dive[@number='{}']".format(dive_number));
    if len(matches) == 0:
        return None;
    return matches[0];


def load_diveprofile_from_xml(xdive) -> DiveProfile:
    xa = xdive.attrib;
    dp = DiveProfile();
    dp.xml_number = int(xa['number']);
    dp.custom_desc = '{} - {} {}'.format(xa['number'], xa['date'], xa['time']);
    # Load gases
    dp.add_gas(Gas.Air())
    # Load points
    xsamples = xdive.findall('divecomputer/sample');
    for xsample in xsamples:
        # eg <sample time='0:40 min' depth='2.5 m' pressure='111.419 bar' />
        tt = re.search('^([0-9]+):([0-9]+) min$',xsample.attrib['time']);
        time = float(tt.group(1)) + (1/60)*float(tt.group(2));
        dd = re.search('^([0-9\.]+) m$',xsample.attrib['depth']);
        depth = float(dd.group(1));
        p = dp._append_point_abstime(time, depth, Gas.Air());
    # Ensure 30 minute surface at end
    dp.remove_surface_at_end();
    dp.append_section(0, 30.0);
    # Recompute all info
    dp.interpolate_points(granularity_mins = 10.0/60.0);
    return dp;

##
## Producing the numbers we need
##


##
## Execute
##
xdive = get_xml_dive(764);
dp = load_diveprofile_from_xml(xdive);
print(dp.description())
print('nr points:', len(dp._points));
for k,v in dp.dive_summary().items():
    print('{}: {}'.format(k,v));
