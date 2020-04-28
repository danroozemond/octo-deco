# Please see LICENSE.md
# Serializing / deserializing DiveProfiles. Taking into account that data coming out of
#   database may be older than current version.
import datetime
import pickle;
import pytz

from . import TissueStateNumpy;

CURRENT_VERSION = 5;


#
# Actual migration
#
def _migrate_up_to_current(from_version, diveprofile):
    if not hasattr(diveprofile, 'created'):
        diveprofile.created = datetime.datetime.now(tz = pytz.timezone('Europe/Amsterdam'));

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
            point.tissue_state = TissueStateNumpy.construct_numpy_from_classic(point.tissue_state, constants);

    # Note that we upgraded
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
