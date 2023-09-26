----------------------------
--BEGIN script transaction--
----------------------------
BEGIN;

DROP TABLE IF EXISTS schema_version;
CREATE TABLE schema_version (
  version_rank INTEGER PRIMARY KEY,
  version TEXT NOT NULL,
  updated_on TEXT NOT NULL
);
INSERT INTO schema_version (version, updated_on) VALUES ('0.0.1', (CURRENT_TIMESTAMP || '+00:00'));

DROP TABLE IF EXISTS transfer;
CREATE TABLE transfer (
    uid TEXT PRIMARY KEY,
    creation_time TEXT DEFAULT (CURRENT_TIMESTAMP || '+00:00') NOT NULL,
    user_input TEXT
);
--------------------------
--END script transaction--
--------------------------
END;
