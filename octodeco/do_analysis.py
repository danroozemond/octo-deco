import sys, math, os, re, pandas as pd, numpy as np;
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

def get_xml_divesites():
    matches = root.findall("./divesites/site");
    r = { m.attrib['uuid'].strip() : m.attrib['name'] for m in matches };
    return r;

def get_xml_dive(dive_number):
    matches = root.findall("./dives/dive[@number='{}']".format(dive_number));
    if len(matches) == 0:
        return None;
    return matches[0];

def xml_parse_time(str_time):
    tt = re.search('^([0-9]+):([0-9]+) min$', str_time);
    return float(tt.group(1)) + (1 / 60) * float(tt.group(2));

def xml_parse_depth(str_depth):
    dd = re.search('^([0-9\.]+) m$', str_depth);
    return float(dd.group(1));

class XmlGasEvents:
    #<event time='0:10 min' type='25' flags='1' name='gaschange' cylinder='0' o2='21.0%' he='35.0%' />
    #<event time='34:50 min' type='25' flags='2' name='gaschange' cylinder='1' o2='50.0%' />
    #<event time='43:40 min' type='25' flags='3' name='gaschange' cylinder='2' o2='80.0%' />
    def __init__(self, xdive):
        xevents = xdive.findall(".//event[@name='gaschange']");
        self._events = [ ( xml_parse_time(xe.attrib['time']), XmlGasEvents._gas_from_xml_event(xe) )
                         for xe in xevents ];
        self._events.sort(key=(lambda t: t[0]));
        assert len(self._events) >= 0;
        self.current_idx = 0;

    def _gas_from_xml_event(xe):
        f = lambda s: float(re.search('^([0-9\.]+)',s).group(1))
        return Gas.Trimix(f(xe.attrib.get('o2', '21.0%')),f(xe.attrib.get('he', '0.0%')));

    def gases(self):
        return set([t[1] for t in self._events]);

    def get_gas(self, time):
        if self.current_idx + 1 < len(self._events) and time >= self._events[self.current_idx+1][0]:
            self.current_idx += 1;
        return self._events[self.current_idx][1];


def load_diveprofile_from_xml(xdive) -> DiveProfile:
    xa = xdive.attrib;
    dp = DiveProfile();
    dp.xml_number = int(xa['number']);
    dp.divesite_uuid = xa['divesiteid'].strip();
    print('Loading dive {}'.format(dp.xml_number));
    dp.custom_desc = '{} - {} {}'.format(xa['number'], xa['date'], xa['time']);
    # Load gases
    xge = XmlGasEvents(xdive);
    for gas in xge.gases():
        dp.add_gas(gas);
    # Load points
    xsamples = xdive.findall('divecomputer/sample');
    for xsample in xsamples:
        # eg <sample time='0:40 min' depth='2.5 m' pressure='111.419 bar' />
        time = xml_parse_time(xsample.attrib['time']);
        depth = xml_parse_depth(xsample.attrib['depth']);
        gas = xge.get_gas(time);
        p = dp._append_point_abstime( time, depth, gas );
        assert p.time >= p.prev.time;
    # Ensure 30 minute surface at end
    dp.remove_surface_at_end();
    dp.append_section(0, 30.0);
    # Recompute all info
    dp.interpolate_points(granularity_mins = 10.0/60.0);
    return dp;

##
## Producing the numbers we need
##
def add_key_data(df, diveprofiles, divesites):
    df['divesite'] = df['number'].map(lambda n : divesites[diveprofiles[n].divesite_uuid]);
    df['depth'] = df['number'].map(lambda n : diveprofiles[n].max_depth());
    df['dive time'] = df['number'].map(lambda n: diveprofiles[ n ].divetime());
    df['gases'] = df['number'].map(lambda n : ','.join([ str(g) for g in diveprofiles[n].gases_carried()]));
    return df;

def add_gf99_data(df, diveprofiles):
    # Do the math
    for _,dp in diveprofiles.items():
        # 1.
        M = np.matrix([ p.deco_info['allGF99s'] for p in dp.points() ]);
        dp.all_GF99s_max_T = np.amax(M, axis=0);
        dp.all_GF99s_max = np.amax(dp.all_GF99s_max_T);
        # 2.
        M = np.matrix([ p.deco_info['allSurfaceGFs'] for p in dp.points() ]);
        dp.all_SurfaceGF99s_max_T = np.amax(M, axis = 0);
        dp.all_SurfaceGF99s_max = np.amax(dp.all_SurfaceGF99s_max_T);
    # Fill the dataframe
    halftimes = next(iter(diveprofiles.values())).deco_model()._constants.N2_HALFTIMES;
    N = 16;
    df[ 'all_GF99s_max' ] = df[ 'number' ].map(lambda n : diveprofiles[n].all_GF99s_max);
    df[ 'all_SurfaceGF99s_max' ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].all_SurfaceGF99s_max);
    for i in range(N):
        df[ 'all_GF99s_max_T{}'.format(halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].all_GF99s_max_T.item(0,i));
    for i in range(N):
        df[ 'all_SurfaceGF99s_max_T{}'.format(halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].all_SurfaceGF99s_max_T.item(0,i));
    # Done
    return df;


##
## Execute
##
# xdive = get_xml_dive(764);
# dp = load_diveprofile_from_xml(xdive);
# print(dp.description())
# print('nr points:', len(dp._points));
# for k,v in dp.dive_summary().items():
#     print('{}: {}'.format(k,v));
# surf_len = dp.length_of_surface_section();
# time_surf = dp._points[-1].time - surf_len;
# pt_surf = dp.find_point_at_time(time_surf);
# assert pt_surf.depth == 0.0;
# assert pt_surf.prev.depth > 0.0;
# print('\nGF on surfacing (time {:.1f}) {} {}'.format(pt_surf.time, pt_surf.deco_info['GF99'], pt_surf.deco_info['SurfaceGF'] ));
# print('All GFs at time {:.1f} : {}'.format(pt_surf.time, pt_surf.deco_info['allGF99s']));
# print('All SGFs at time {:.1f} : {}'.format(pt_surf.time, pt_surf.deco_info['allSurfaceGFs']));

diveprofiles = { n: load_diveprofile_from_xml(get_xml_dive(n)) for n in range(604, 607) };
dd = { n : { 'number' : n, 'description': dp.description() }
       for n, dp in diveprofiles.items() };
dfout = pd.DataFrame(dd).transpose();
dfout = add_key_data(dfout, diveprofiles, get_xml_divesites());
dfout = add_gf99_data(dfout, diveprofiles);

print(dfout.head());
print('Writing output file...');
dfout.to_excel(os.path.join(ANALYSIS_PATH,'output.xlsx'));
print('Done.');