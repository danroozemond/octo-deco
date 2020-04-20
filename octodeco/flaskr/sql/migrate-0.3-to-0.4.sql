/* for testing
insert into dives(dive_desc, user_id, dive)
   select dive_desc, '9d6e3dbb-0ee4-458a-90a7-bf1e3c1d56dd', dive
   from dives where dive_id=2;
*/
/* rename old table */
ALTER TABLE dives RENAME TO dives_old;
/* create new dives table */
CREATE TABLE dives (
  dive_id INTEGER PRIMARY KEY AUTOINCREMENT,
  dive_desc TEXT,
  user_id INTEGER NOT NULL,
  is_demo BOOL,
  dive BLOB NOT NULL,
  last_update DATETIME
);
/* create sessions table */
CREATE TABLE sessions (
  session_id TEXT NOT NULL,
  user_id INTEGER
);
/* fill sessions table */
INSERT INTO sessions(session_id)
SELECT DISTINCT(user_id)
FROM dives_old;
UPDATE sessions SET user_id=rowid;
/* create users table */
CREATE TABLE users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  google_sub TEXT,
  google_given_name TEXT,
  google_picture TEXT
);
/* also need to fill users table */
insert into users(user_id)
select distinct user_id from sessions;
/* fill new dives table */
insert into dives(dive_id, dive_desc, user_id, is_demo, dive, last_update)
SELECT d.dive_id, d.dive_desc, s.user_id, 0, d.dive, datetime('now')
FROM dives_old d LEFT JOIN sessions s
on d.user_id=s.session_id;
/* drop old dives table */
DROP TABLE dives_old;
