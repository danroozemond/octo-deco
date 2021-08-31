# Please see LICENSE.md
from flask import abort;

from . import db;
from .user import get_user_details;
from .app import cache;

from octodeco.deco import DiveProfileSer;

# All functions in this file are focused on the current user, no need
# to explicitly supply

#
# batch migration
#
def migrate_all_profiles_to_latest():
    assert get_user_details().is_admin;
    cur = db.get_db().cursor();
    cur2 = db.get_db().cursor();
    rows = cur.execute('''
        SELECT dive_id, dive
        FROM dives
        ''');
    result = {'Timeout': False}; cnt = 0;
    for row in rows:
        dp, oldv, newv = DiveProfileSer.loads_with_version_info(row['dive']);
        if oldv == newv:
            continue;
        # Keep track
        strv = '{} -> {}'.format(oldv, newv);
        result[strv] = result.get(strv, 0) + 1;
        cnt += 1;
        # Do update
        cur2.execute('''
            UPDATE dives
            SET dive = ? 
            WHERE dive_id = ?
        ''', [ DiveProfileSer.dumps(dp), row['dive_id'] ] );
        # Limit, to avoid timeouts
        if cnt > 100:
            result['timeout'] = True;
            break;
    # Done
    return result;


