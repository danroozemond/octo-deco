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
    # Deco model
    xdm = xdive.find('divecomputer/extradata[@key="Deco model"]');
    gf_low = 35; gf_high = 70;
    if xdm is not None:
        m = re.match('^GF ([0-9]+)/([0-9]+)$', xdm.attrib[ 'value' ].strip());
        if m is not None:
            gf_low = int(m.group(1));
            gf_high = int(m.group(2));
    # Initiate DiveProfile
    dp = DiveProfile(gf_low = gf_low, gf_high = gf_high);
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
    df['deco_model'] = df['number'].map(lambda n : diveprofiles[n]._desc_deco_model_display);
    df['integral supersaturation']= df['number'].map(lambda n : diveprofiles[n].integral_supersaturation());
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
        # 3
        surf_len = dp.length_of_surface_section();
        time_surf = dp._points[-1].time - surf_len;
        pt_surf = dp.find_point_at_time(time_surf);
        dp.GF99s_at_surfacing = pt_surf.deco_info['allGF99s'];
        dp.GF99_at_surfacing = max(pt_surf.deco_info['allGF99s']);
        pt = dp.find_point_at_time(time_surf + 10.0);
        dp.GF99s_at_surfacing_plus_10 = pt.deco_info[ 'allGF99s' ];
        dp.GF99_at_surfacing_plus_10 = max(pt.deco_info[ 'allGF99s' ]);
        pt = dp.find_point_at_time(time_surf + 30.0);
        dp.GF99s_at_surfacing_plus_30 = pt.deco_info[ 'allGF99s' ];
        dp.GF99_at_surfacing_plus_30 = max(pt.deco_info[ 'allGF99s' ]);
    # Fill the dataframe
    halftimes = next(iter(diveprofiles.values())).deco_model()._constants.N2_HALFTIMES;
    N = 16;
    df[ 'all_GF99s_max' ] = df[ 'number' ].map(lambda n : diveprofiles[n].all_GF99s_max);
    df[ 'all_SurfaceGF99s_max' ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].all_SurfaceGF99s_max);
    df[ 'GF99_at_surfacing' ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].GF99_at_surfacing);
    df[ 'GF99_at_surfacing_plus_10' ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].GF99_at_surfacing_plus_10);
    df[ 'GF99_at_surfacing_plus_30' ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].GF99_at_surfacing_plus_30);
    for i in range(N):
        df[ 'all_GF99s_max_T{}'.format(halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].all_GF99s_max_T.item(0,i));
    for i in range(N):
        df[ 'all_SurfaceGF99s_max_T{}'.format(halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].all_SurfaceGF99s_max_T.item(0,i));
    for i in range(N):
        df[ 'GF99_at_surfacing_T{}'.format(halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].GF99s_at_surfacing[i]);
    for i in range(N):
        df[ 'GF99_at_surfacing_plus_10_T{}'.format(halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].GF99s_at_surfacing_plus_10[i]);
    for i in range(N):
        df[ 'GF99_at_surfacing_plus_30_T{}'.format(halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].GF99s_at_surfacing_plus_30[i]);
    # Done
    return df;

def add_gf99_data_count_time(df, diveprofiles):
    halftimes = next(iter(diveprofiles.values())).deco_model()._constants.N2_HALFTIMES;
    N = 16; perc_thresholds = [ 10.0, 20.0 ];
    # Do the math
    for _,dp in diveprofiles.items():
        # 1.
        cumuls = { pthr : np.array([ 0.0 for i in range(N) ]) for pthr in perc_thresholds };
        for p in dp.points():
            if p.depth >= 2.0:
                gf99s = p.deco_info['allGF99s'];
                indics = { pthr :
                               np.array([ 1.0 if gf99s[i] > pthr else 0.0 for i in range(N) ])
                               for pthr in perc_thresholds };
                for pthr in perc_thresholds:
                    cumuls[pthr] = cumuls[pthr] + p.duration*indics[pthr];
        dp.cumuls = cumuls;
    # Fill the dataframe
    # df[ 'all_GF99s_max' ] = df[ 'number' ].map(lambda n : diveprofiles[n].all_GF99s_max);
    for pthr in perc_thresholds:
        for i in range(N):
            df[ 'cumul_GF99_over_{:.0f}%_T{}'.format(pthr,halftimes[i]) ] = df[ 'number' ].map(lambda n: diveprofiles[ n ].cumuls[pthr][i])
    # Done
    return df;

##
## Execute
##
diveprofiles = { n: load_diveprofile_from_xml(get_xml_dive(n)) for n in range(604, 607) };
dd = { n : { 'number' : n, 'description': dp.description() }
       for n, dp in diveprofiles.items() };
dfout = pd.DataFrame(dd).transpose();
dfout = add_key_data(dfout, diveprofiles, get_xml_divesites());
dfout = add_gf99_data(dfout, diveprofiles);
dfout = add_gf99_data_count_time(dfout, diveprofiles);

print(dfout.head());
print('Writing output file...');
dfout.to_excel(os.path.join(ANALYSIS_PATH,'output.xlsx'));
print('Done.');