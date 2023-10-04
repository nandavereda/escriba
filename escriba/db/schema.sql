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

DROP TABLE IF EXISTS transfer_job;
CREATE TABLE transfer_job (
    uid TEXT PRIMARY KEY,
    creation_time TEXT DEFAULT (CURRENT_TIMESTAMP || + '+00:00') NOT NULL,
    modified_time TEXT,
    transfer_uid TEXT NOT NULL,
    job_state_uid INTEGER NOT NULL,

    FOREIGN KEY (transfer_uid)
        REFERENCES transfer (uid),
    FOREIGN KEY (job_state_uid)
        REFERENCES job_state (uid)
);
CREATE TRIGGER update_transfer_job_modified_time
    AFTER UPDATE
    OF job_state_uid
    ON transfer_job
    FOR EACH ROW
BEGIN
    UPDATE transfer_job SET modified_time = (CURRENT_TIMESTAMP || '+00:00');
END;

DROP TABLE IF EXISTS job_state;
CREATE TABLE job_state (
    uid INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
INSERT INTO job_state (uid, name) VALUES
    (1, "PENDING"),
    (2, "EXECUTING"),
    (3, "SUCCEEDED"),
    (4, "FAILED")
;

DROP TABLE IF EXISTS webpage;
CREATE TABLE webpage (
  uid TEXT PRIMARY KEY,
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  creation_time TEXT DEFAULT (CURRENT_TIMESTAMP || '+00:00') NOT NULL,
  modified_time TEXT
);
CREATE TRIGGER update_webpage_modified_time
    AFTER UPDATE
    OF title
    ON webpage
    FOR EACH ROW
BEGIN
    UPDATE webpage SET modified_time = (CURRENT_TIMESTAMP || '+00:00');
END;

DROP TABLE IF EXISTS webpage_transfer_job_association;
CREATE TABLE webpage_transfer_job_association (
    webpage_uid TEXT,
    transfer_job_uid TEXT,
    PRIMARY KEY (webpage_uid, transfer_job_uid)
);
--------------------------
--END script transaction--
--------------------------
END;
