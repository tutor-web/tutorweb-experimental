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
    user_id                  INTEGER,
    FOREIGN KEY (hostDomain, user_id) REFERENCES "user"(hostDomain, user_id),
    path                     TEXT,
    FOREIGN KEY (hostDomain, path) REFERENCES tutorial(hostDomain, path),
    PRIMARY KEY (hostDomain, user_id, path),

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
    lecture_name             TEXT,
    PRIMARY KEY (hostDomain, path, lecture_name),

    title                    TEXT,

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  lecture IS 'Lectures sit within a tutorial';


CREATE TABLE IF NOT EXISTS stage (
    hostDomain               TEXT,
    path                     TEXT,
    lecture_name             TEXT,
    FOREIGN KEY (hostDomain, path, lecture_name) REFERENCES lecture(hostDomain, path, lecture_name),
    stage_name               TEXT,
    version                  INTEGER,
    PRIMARY KEY (hostDomain, path, lecture_name, stage_name, version),

    stage_id                 SERIAL,
    UNIQUE (stage_id),

    title                    TEXT NOT NULL,
    stage_setting_spec       JSONB,
    material_tags            TEXT[] NOT NULL DEFAULT '{}',

    next_version             INTEGER NULL,
    FOREIGN KEY (hostDomain, path, lecture_name, stage_name, next_version)
        REFERENCES stage(hostDomain, path, lecture_name, stage_name, version),

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  stage IS 'An individual stage in this lecture, and the tags for relevant content within';
COMMENT ON COLUMN stage.stage_id IS 'A shorthand to avoid refering to the entire compound key';
COMMENT ON COLUMN stage.stage_setting_spec IS 'dict of setting key to a combination of:'
    '* value: Fixed value / mean value for gamma distribution'
    '* shape: Shape of gamma curve, if set will choose value for each student from gamma curve'
    '* max: Maximum value, if set will choose value between [0, value_max)'
    '* min: Minimum value, applies a lower bound to anything chosen by max'
    '...or "deleted", if this stage is now removed';
COMMENT ON COLUMN stage.next_version IS 'If this stage has been replaced by a new version, this field is non-null';


CREATE TABLE IF NOT EXISTS stage_setting (
    stage_id                 INTEGER NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    hostDomain               TEXT,
    user_id                  INTEGER,
    FOREIGN KEY (hostDomain, user_id) REFERENCES "user"(hostDomain, user_id),
    key                      TEXT,
    PRIMARY KEY (stage_id, hostDomain, user_id, key),

    value                    TEXT,

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  stage_setting IS 'All chosen settings for a stage, generic and per-student';
COMMENT ON COLUMN stage_setting.user_id IS 'Student setting is for, or one of the special students:'
     '"(registered)" for a generic registed student,'
     '"(any)" for any student';

-- TODO: Answer summary per student
-- TODO: Answer summary per-lecture, to use for difficulty
-- TODO: Allocations, how to do it?
-- * GetQuestion based on public ID (which may be out of date)
-- * Get all questions allocated for a lecture
-- * Update/create allocations, return list
--    ==> Ideallyquestion URI:index:version)
--    Encrypt URI:index:version with random AES string for each student?


COMMIT;
