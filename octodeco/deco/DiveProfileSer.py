# Please see LICENSE.md
# Serializing / deserializing DiveProfiles. Taking into account that data coming out of
#   database may be older than current version.
import pickle;
import datetime, pytz;

CURRENT_VERSION = 1;


#
# Actual migration
#
def _migrate_up_to_current(from_version, diveprofile):
    if not hasattr(diveprofile, 'created'):
        diveprofile.created = datetime.datetime.now(tz = pytz.timezone('Europe/Amsterdam'));

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

