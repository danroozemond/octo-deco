CREATE TABLE dives (
  dive_id INTEGER PRIMARY KEY AUTOINCREMENT,
  dive_desc TEXT,
  user_id INTEGER NOT NULL,
  is_demo BOOL,
  dive BLOB NOT NULL,
  last_update DATETIME,
  is_public BOOL,
  is_ephemeral BOOL,
  object_version INTEGER DEFAULT 0
);
