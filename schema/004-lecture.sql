BEGIN;

CREATE TABLE IF NOT EXISTS tutorial (
    hostDomain               TEXT,
    FOREIGN KEY (hostDomain) REFERENCES host(hostDomain),
    path                     TEXT,
    PRIMARY KEY (hostDomain, path),

    title                    TEXT,

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastUpdate_trigger('tutorial');
COMMENT ON TABLE  tutorial IS 'Tree structure for all tutorials';


CREATE TABLE IF NOT EXISTS subscription (
    hostDomain               TEXT,
    FOREIGN KEY (hostDomain) REFERENCES host(hostDomain),
    userName                 TEXT,
    FOREIGN KEY (hostDomain, userName) REFERENCES student(hostDomain, userName),
    path                     TEXT,
    FOREIGN KEY (hostDomain, path) REFERENCES tutorial(hostDomain, path),
    PRIMARY KEY (hostDomain, userName, path),

    hidden                   BOOLEAN NOT NULL DEFAULT 'f',
    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastUpdate_trigger('subscription');
COMMENT ON TABLE  subscription IS 'Student<->tutorial subscriptions';


CREATE TABLE IF NOT EXISTS lecture (
    hostDomain               TEXT,
    FOREIGN KEY (hostDomain) REFERENCES host(hostDomain),
    path                     TEXT,
    FOREIGN KEY (hostDomain, path) REFERENCES tutorial(hostDomain, path),
    name                     TEXT, -- TODO: This "name" appears in other tables and is very confusing
    version                  INTEGER,
    PRIMARY KEY (hostDomain, path, name, version),

    title                    TEXT,

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  lecture IS 'Lectures sit within a tutorial';


CREATE TABLE IF NOT EXISTS lectureStage ( -- TODO: Just "stage" enough?
    lectureStageId           SERIAL PRIMARY KEY,

    hostDomain               TEXT,
    path                     TEXT,
    name                     TEXT,
    version                  INTEGER,
    FOREIGN KEY (hostDomain, path, name, version) REFERENCES lecture(hostDomain, path, name, version),
    stage                    TEXT, -- TODO: More consistency vis. "name" as above?
    UNIQUE (hostDomain, path, version, stage),

    title                    TEXT,

    materialTags             TEXT[] NOT NULL DEFAULT '{}',
    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  lectureStage IS 'An individual stage in this lecture, and the tags for relevant content within';


CREATE TABLE IF NOT EXISTS lectureGlobalSettings (
    hostDomain               TEXT,
    path                     TEXT,
    name                     TEXT,
    version                  INTEGER,
    FOREIGN KEY (hostDomain, path, name, version) REFERENCES lecture(hostDomain, path, name, version),
    variant                  TEXT NOT NULL DEFAULT '',
    key                      TEXT,
    PRIMARY KEY (hostDomain, path, name, version, variant, key),

    creationDate             TIMESTAMP NOT NULL DEFAULT NOW(),
    value                    TEXT,
    shape                    FLOAT,
    max                      FLOAT,
    min                      FLOAT
);
COMMENT ON TABLE  lectureGlobalSettings IS 'All settings set for a lecture over time, for every student';
COMMENT ON COLUMN lectureGlobalSettings.variant IS 'Variant, e.g. "registered" or all-purpose "". We will choose one for a student';
COMMENT ON COLUMN lectureGlobalSettings.value IS 'Fixed value / mean value for gamma distribution';
COMMENT ON COLUMN lectureGlobalSettings.shape IS 'Shape of gamma curve, if set will choose value for each student from gamma curve';
COMMENT ON COLUMN lectureGlobalSettings.max IS 'Maximum value, if set will choose value between [0, value_max)';
COMMENT ON COLUMN lectureGlobalSettings.min IS 'Minimum value, applies a lower bound to anything chosen by max';


CREATE TABLE IF NOT EXISTS lectureStudentSettings (
    hostDomain               TEXT,
    path                     TEXT,
    name                     TEXT,
    version                  INTEGER,
    FOREIGN KEY (hostDomain, path, name, version) REFERENCES lecture(hostDomain, path, name, version),
    userName                  TEXT,
    FOREIGN KEY (hostDomain, userName) REFERENCES student(hostDomain, userName),
    key                      TEXT,
    PRIMARY KEY (hostDomain, path, name, version, userName, key),

    -- NB: Not part of the primary key, we only choose one.
    variant                  TEXT NOT NULL DEFAULT '',

    creationDate             TIMESTAMP NOT NULL DEFAULT NOW(),
    value                    TEXT
);
COMMENT ON TABLE  lectureStudentSettings IS 'All settings assigned to a student';
COMMENT ON COLUMN lectureStudentSettings.variant IS 'Variant, e.g. "registered" or all-purpose ""';


-- TODO: Answer summary per student
-- TODO: Answer summary per-lecture, to use for difficulty
-- TODO: Allocations, how to do it?
-- * GetQuestion based on public ID (which may be out of date)
-- * Get all questions allocated for a lecture
-- * Update/create allocations, return list
--    ==> Ideallyquestion URI:index:version)
--    Encrypt URI:index:version with random AES string for each student?


COMMIT;
