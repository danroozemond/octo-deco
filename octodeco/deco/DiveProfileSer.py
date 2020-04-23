# Please see LICENSE.md
# Serializing / deserializing DiveProfiles. Taking into account that data coming out of
#   database may be older than current version.
import pickle;

from . import DiveProfile;


# pickle.loads & pickle.dumps

class DiveProfileSer():
