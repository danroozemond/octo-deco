ALTER TABLE users ADD COLUMN last_activity DATETIME;
UPDATE users SET last_activity=datetime('now');
