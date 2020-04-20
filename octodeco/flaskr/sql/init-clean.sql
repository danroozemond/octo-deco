CREATE TABLE dives (
  dive_id INTEGER PRIMARY KEY AUTOINCREMENT,
  dive_desc TEXT,
  user_id INTEGER NOT NULL,
  is_demo BOOL,
  dive BLOB NOT NULL,
  last_update DATETIME
);
CREATE TABLE users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  google_sub TEXT,
  google_given_name TEXT,
  google_picture TEXT
);
CREATE TABLE sessions (
  session_id TEXT NOT NULL,
  user_id INTEGER
);
