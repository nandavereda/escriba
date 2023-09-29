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
    transfer_job_state_uid INTEGER NOT NULL,

    FOREIGN KEY (transfer_uid)
        REFERENCES transfer (uid),
    FOREIGN KEY (transfer_job_state_uid)
        REFERENCES transfer_job_state (uid)
);
CREATE TRIGGER update_transfer_job_modified_time
    AFTER UPDATE
    OF transfer_job_state_uid
    ON transfer_job
    FOR EACH ROW
BEGIN
    UPDATE transfer_job SET modified_time = (CURRENT_TIMESTAMP || '+00:00');
END;

DROP TABLE IF EXISTS transfer_job_state;
CREATE TABLE transfer_job_state (
    uid INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
INSERT INTO transfer_job_state (uid, name) VALUES
    (1, "PENDING"),
    (2, "EXECUTING"),
    (3, "SUCCEEDED"),
    (4, "FAILED")
;
--------------------------
--END script transaction--
--------------------------
END;
