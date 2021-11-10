CREATE TABLE dives (
  dive_id TEXT,
  dive_desc TEXT,
  user_id TEXT NOT NULL,
  is_demo BOOL,
  dive BLOB NOT NULL,
  last_update DATETIME,
  is_public BOOL DEFAULT 1,
  is_ephemeral BOOL,
  object_version INTEGER DEFAULT 0
);
