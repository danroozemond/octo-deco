import base64;
from fastapi import APIRouter, Depends
from sqlite3 import Connection
from .app import get_db;
from typing import Optional
from pydantic import BaseModel

router = APIRouter(
    prefix="/retrieve"
);

# Probably when I grow up I want to use SQLAlchemy
class DBDive(BaseModel):
    dive_id: int
    user_id: Optional[int] = None
    dive_desc: str
    is_public: bool
    dive_serialized: Optional[int] = None

    @staticmethod
    def from_row(row):
        if row is None:
            return None;
        r = DBDive(dive_id = row[ 'dive_id' ], dive_desc = row[ 'dive_desc' ], is_public = row[ 'is_public' ]);
        if 'user_id' in row.keys():
            r.user_id = row['user_id'];
        if 'dive' in row.keys():
            r.dive_serialized = base64.b64encode(row['dive']);
        return r;


@router.get("/dive_count/")
def get_dive_count(user_id: int, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
            SELECT COUNT(*)
            FROM dives
            WHERE user_id = ?
            ''', [ user_id ]
                );
    return { 'dive_count': cur.fetchone()[ 0 ] };


@router.get("/all/")
def get_all_dives(user_id: int, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
        SELECT dive_id, dive_desc, is_public
        FROM dives
        WHERE user_id = ? AND NOT is_ephemeral
        ''', [ user_id ]
                );
    rows = cur.fetchall();
    return [ DBDive.from_row(row) for row in rows ];


@router.get("/any/")
def get_any_dive(user_id: int, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
        SELECT dive_id, dive_desc, is_public
        FROM dives
        WHERE user_id = ? AND NOT is_ephemeral
        ORDER BY dive_id ASC
        LIMIT 1
        ''', [ user_id ]
                );
    row = cur.fetchone();
    return DBDive.from_row(row);


@router.get("/get/")
def get_one_dive(user_id: int,dive_id:int, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
        SELECT user_id, dive_id, dive_desc, dive, is_public
        FROM dives
        WHERE dive_id = ? and (is_public or user_id = ?) 
        ''', [ dive_id, user_id ]
                      );
    row = cur.fetchone();
    return DBDive.from_row(row);
