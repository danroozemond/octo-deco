import os
import sqlite3
from fastapi import FastAPI, Depends

app = FastAPI()

DB_SQLITE = os.environ.get('DB_SQLITE');


# Database interface
def get_db():
    db = sqlite3.connect(
        DB_SQLITE,
        detect_types = sqlite3.PARSE_DECLTYPES,
        isolation_level = None,
        check_same_thread = False
    )
    db.row_factory = sqlite3.Row
    try:
        yield db;
    finally:
        db.close();


# Todo remove this
@app.get("/")
def root():
    return {"message": "Hello World"}


# Here the magic happens
from . import dive_retrieve;
app.include_router(dive_retrieve.router)
