# Please see LICENSE.md
# Serializing / deserializing DiveProfiles. Taking into account that data coming out of
#   database may be older than current version.
import datetime
import pickle;

import pytz

CURRENT_VERSION = 16;


#
# Actual migration
#
def _migrate_up_to_current(from_version, diveprofile):
    if not hasattr(diveprofile, 'created'):
        diveprofile.created = datetime.datetime.now(tz = pytz.timezone('Europe/Amsterdam'));
    if not hasattr(diveprofile, '_gas_switch_mins'):
        diveprofile._gas_switch_mins = 3.0;
    if not hasattr(diveprofile, '_last_stop_depth'):
        diveprofile._last_stop_depth = 3;
    if not hasattr(diveprofile, '_max_pO2_deco'):
        diveprofile._max_pO2_deco = 1.60;
    if not hasattr(diveprofile, '_gas_consmp_bottom'):
        diveprofile._gas_consmp_bottom = 20.0;
    if not hasattr(diveprofile, '_gas_consmp_deco'):
        diveprofile._gas_consmp_deco = 20.0;
    if not hasattr(diveprofile, '_gas_consmp_emerg_factor'):
        diveprofile._gas_consmp_emerg_factor = 4.0;
    if not hasattr(diveprofile, '_gas_consmp_emerg_mins'):
        diveprofile._gas_consmp_emerg_mins = 4.0;

    # None
    for attrname in [ 'custom_desc', 'add_custom_desc', '_cylinders_used' ]:
        if not hasattr(diveprofile, attrname):
            setattr(diveprofile, attrname, None);

    # Bool
    for attrname in [ 'is_demo_dive', 'is_public', 'is_ephemeral'  ]:
        if not hasattr(diveprofile, attrname):
            setattr(diveprofile, attrname, False);

    # Point attributes
    for point in diveprofile.points():
        if not hasattr(point, 'is_ascent_point'):
            point.is_ascent_point = False;
        if not hasattr(point, 'cns_perc'):
            point.cns_perc = 0.0;
        if not hasattr(point, '_gas_consumption_info'):
            point.set_updated_gas_consumption_info(diveprofile);

    # v8
    if hasattr(diveprofile, '_deco_model'):
        diveprofile._deco_model = None;

    # Note that we upgraded
    dive_id = getattr(diveprofile, 'dive_id', None);
    print('Upgraded dive {} from v{} to v{}'.format(dive_id, from_version, CURRENT_VERSION));
    diveprofile.db_version = CURRENT_VERSION;
    diveprofile.update_deco_info();


#
# Interface functions
#
def _loads_only(blob):
    return pickle.loads(blob);


def _migrate(diveprofile):
    version = getattr(diveprofile, 'db_version', 0);
    if version != CURRENT_VERSION:
        _migrate_up_to_current(version, diveprofile);


def loads_with_version_info(blob):
    dp = _loads_only(blob);
    oldversion = getattr(dp, 'db_version', 0);
    _migrate(dp);
    newversion = dp.db_version;
    return dp, oldversion, newversion;


def loads(blob):
    # .. = load and migrate
    dp, _, _ = loads_with_version_info(blob);
    return dp;


def dumps(diveprofile):
    return pickle.dumps(diveprofile);
