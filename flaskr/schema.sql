DROP TABLE IF EXISTS dives;

CREATE TABLE dives (
  dive_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  dive BLOB NOT NULL
);

