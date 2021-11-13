import base64;
from fastapi import APIRouter, Depends
from sqlite3 import Connection
from .app import get_db;
from .dive import DBDive;
import uuid;

router = APIRouter(
    prefix="/dive/write"
);


def _store_dive_update(db: Connection, dbdv: DBDive) -> int:
    cur = db.cursor();
    cur.execute('''
        UPDATE dives
        SET dive = ?, dive_desc = ?, is_demo = ?, is_ephemeral = ?,  is_public = ?, object_version = ?, 
        last_update = datetime('now')
        WHERE dive_id = ? AND user_id = ?;
        ''', [ base64.b64decode(dbdv.dive_serialized.encode('utf-8')), dbdv.dive_desc,
               dbdv.is_demo, dbdv.is_ephemeral, dbdv.is_public, dbdv.object_version,
               dbdv.dive_id, dbdv.user_id ]
               );
    return cur.rowcount;


def _store_dive_new(db: Connection, dbdv: DBDive) -> DBDive:
    cur = db.cursor();
    dbdv.dive_id = 'dv_'+ str(uuid.uuid4()).replace('-','_');
    cur.execute('''
        INSERT INTO dives(user_id, dive_id, dive)
        VALUES (?, ?, 'xx');
        ''', [ dbdv.user_id, dbdv.dive_id ] );
    _store_dive_update(db, dbdv);
    return dbdv;


@router.put("/store/", response_model=DBDive)
def store_dive(dive: DBDive, db: Connection = Depends(get_db)):
    # No dive_id available -> store
    if dive.dive_id is None:
        dive = _store_dive_new(db, dive);
        return dive;
    # dive_id available -> first try to update.
    try:
        _store_dive_update(db, dive);
        return dive;
    except AttributeError:
        dive = _store_dive_new(db, dive);
        return dive;


@router.delete("/delete/")
def delete_dive(dive_id: str, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
        DELETE
        FROM dives
        WHERE dive_id = ?
        ''', [ dive_id ]
                      );
    return { 'affected_count': cur.rowcount };
