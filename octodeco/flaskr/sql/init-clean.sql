CREATE TABLE dives (
  dive_id INTEGER PRIMARY KEY AUTOINCREMENT,
  dive_desc TEXT,
  user_id INTEGER NOT NULL,
  is_demo BOOL,
  dive BLOB NOT NULL
);
CREATE TABLE users (
  user_id INTEGER,
  google_email TEXT
);
CREATE TABLE sessions (
  session_id TEXT NOT NULL,
  user_id INTEGER
);
