from fastapi import APIRouter, Depends, Response, status;
from sqlite3 import Connection;
from typing import List;
from .app import get_db;
from .dive import DBDive;

router = APIRouter(
    prefix = "/dive/retrieve"
);


@router.get("/count/")
def get_dive_count(user_id: int, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
            SELECT COUNT(*)
            FROM dives
            WHERE user_id = ?
            ''', [ user_id ]
                );
    return {'dive_count': cur.fetchone()[ 0 ]};


@router.get("/all/", response_model = List[ DBDive ])
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


@router.get("/any/", response_model = DBDive)
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


@router.get("/get/", response_model = DBDive)
def get_one_dive(dive_id: str, response: Response, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
        SELECT user_id, dive_id, dive_desc, dive, is_public
        FROM dives
        WHERE dive_id = ? 
        ''', [ dive_id ]
                );
    row = cur.fetchone();
    if row is None:
        response.status_code = status.HTTP_404_NOT_FOUND;
        return None;
    else:
        return DBDive.from_row(row);


@router.get("/outdated_object_versions/")
def get_all_all_dives(latest_version: int, db: Connection = Depends(get_db)):
    cur = db.cursor();
    cur.execute('''
        SELECT dive_id
        FROM dives
        WHERE object_version < ?
        ORDER BY last_update ASC
        LIMIT 1000''',
                [ latest_version ]);
    result = [ row[ 'dive_id' ] for row in cur.fetchall() ];
    return result;
