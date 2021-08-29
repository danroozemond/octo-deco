import os
import sqlite3
from sqlite3 import Connection
from fastapi import FastAPI, Depends

app = FastAPI()

DB_SQLITE = os.environ.get('DB_SQLITE');


# Database interface
def get_db():
    db = sqlite3.connect(
        DB_SQLITE,
        detect_types = sqlite3.PARSE_DECLTYPES,
        isolation_level = None
    )
    db.row_factory = sqlite3.Row
    try:
        yield db;
    finally:
        db.close();

@app.get("/")
def root(db: Connection = Depends(get_db)):
    print(db);
    return {"message": "Hello World"}

