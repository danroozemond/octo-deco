# Please see LICENSE.md
# Serializing / deserializing DiveProfiles. Taking into account that data coming out of
#   database may be older than current version.
import datetime
import pickle;

import pytz

from . import TissueStateNumpy, TissueStateCython, TissueStateClassic;

CURRENT_VERSION = 8;


#
# Actual migration
#
def _migrate_up_to_current(from_version, diveprofile):
    if not hasattr(diveprofile, 'created'):
        diveprofile.created = datetime.datetime.now(tz = pytz.timezone('Europe/Amsterdam'));
    if not hasattr(diveprofile, '_gas_switch_mins'):
        diveprofile._gas_switch_mins = 3.0;
    if not hasattr(diveprofile, '_max_pO2_deco'):
        diveprofile._max_pO2_deco = 1.60;

    # None
    for attrname in [ 'custom_desc', 'add_custom_desc' ]:
        if not hasattr(diveprofile, attrname):
            setattr(diveprofile, attrname, None);

    # Bool
    for attrname in [ 'is_demo_dive', 'is_public'  ]:
        if not hasattr(diveprofile, attrname):
            setattr(diveprofile, attrname, False);

    # Tissue State
    if from_version < 5:
        constants = diveprofile.deco_model()._constants;
        for point in diveprofile.points():
            iptts = point.tissue_state._state if type(point.tissue_state) == TissueStateClassic.TissueState \
                    else point.tissue_state;
            point.tissue_state = TissueStateNumpy.construct_numpy_from_classic(iptts, constants);
    if from_version < 6:
        constants = diveprofile.deco_model()._constants;
        for point in diveprofile.points():
            point.tissue_state = TissueStateCython.construct_cython_from_numpy(point.tissue_state, constants);

    # Point attributes
    for point in diveprofile.points():
        if not hasattr(point, 'is_ascent_point'):
            point.is_ascent_point = False;

    # v8
    if hasattr(diveprofile, '_deco_model'):
        diveprofile._deco_model = None;

    # Note that we upgraded
    dive_id = getattr(diveprofile, 'dive_id', -1);
    print('Upgraded dive {} from v{} to v{}'.format(dive_id, from_version, CURRENT_VERSION));
    diveprofile.db_version = CURRENT_VERSION;


#
# Interface functions
#
def _loads_only(blob):
    return pickle.loads(blob);


def _migrate(diveprofile):
    version = getattr(diveprofile, 'db_version', 0);
    if version != CURRENT_VERSION:
        _migrate_up_to_current(version, diveprofile);


def loads(blob):
    # .. = load and migrate
    dp = _loads_only(blob);
    _migrate(dp);
    return dp;


def dumps(diveprofile):
    return pickle.dumps(diveprofile);
