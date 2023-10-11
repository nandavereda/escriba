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

DROP TABLE IF EXISTS webpage_job;
CREATE TABLE webpage_job (
    uid TEXT PRIMARY KEY,
    creation_time TEXT DEFAULT (CURRENT_TIMESTAMP || + '+00:00') NOT NULL,
    modified_time TEXT,
    webpage_uid TEXT NOT NULL,
    job_state_uid INTEGER NOT NULL,

    FOREIGN KEY (webpage_uid)
        REFERENCES webpage (uid),
    FOREIGN KEY (job_state_uid)
        REFERENCES job_state (uid)
);
CREATE TRIGGER update_webpage_job_modified_time
    AFTER UPDATE
    OF job_state_uid
    ON webpage_job
    FOR EACH ROW
BEGIN
    UPDATE webpage_job SET modified_time = (CURRENT_TIMESTAMP || '+00:00');
END;

DROP TABLE IF EXISTS snapshot;
CREATE TABLE snapshot (
    uid TEXT PRIMARY KEY,
    webpage_uid TEXT NOT NULL,
    strategy_uid INTEGER NOT NULL,
    job_state_uid INTEGER NOT NULL,
    creation_time TEXT DEFAULT (CURRENT_TIMESTAMP || '+00:00') NOT NULL,
    modified_time TEXT,
    result TEXT,

    FOREIGN KEY (webpage_uid)
        REFERENCES webpage (uid),
    FOREIGN KEY (strategy_uid)
        REFERENCES strategy (uid),
    FOREIGN KEY (job_state_uid)
        REFERENCES job_state (uid)
);
CREATE TRIGGER update_snapshot_modified_time
    AFTER UPDATE
    OF job_state_uid,result
    ON snapshot
    FOR EACH ROW
BEGIN
    UPDATE snapshot SET modified_time = (CURRENT_TIMESTAMP || '+00:00');
END;

DROP TABLE IF EXISTS strategy;
CREATE TABLE strategy (
    uid INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
INSERT INTO strategy (uid, name) VALUES
    (1, "archive-dot-org"),
    (2, "title"),
    (3, "favicon"),

    (10, "curl"),
    (11, "wget"),
    (12, "warc"),

    (20, "pdf"),
    (21, "screenshot"),
    (22, "dom"),

    (30, "singlefile"),
    (31, "readability"),
    (32, "mercury"),

    (40, "git"),
    (41, "yt-dlp")
;
--------------------------
--END script transaction--
--------------------------
END;
