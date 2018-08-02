BEGIN;

CREATE TABLE IF NOT EXISTS tutorial (
    host_id                  INTEGER,
    FOREIGN KEY (host_id) REFERENCES host(host_id),
    path                     TEXT,
    PRIMARY KEY (host_id, path),

    title                    TEXT,

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastUpdate_trigger('tutorial');
COMMENT ON TABLE  tutorial IS 'Tree structure for all tutorials';


CREATE TABLE IF NOT EXISTS subscription (
    host_id                  INTEGER,
    FOREIGN KEY (host_id) REFERENCES host(host_id),
    user_id                  INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id),
    path                     TEXT,
    FOREIGN KEY (host_id, path) REFERENCES tutorial(host_id, path),
    PRIMARY KEY (host_id, user_id, path),

    hidden                   BOOLEAN NOT NULL DEFAULT 'f',
    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastUpdate_trigger('subscription');
COMMENT ON TABLE  subscription IS 'Student<->tutorial subscriptions';


CREATE TABLE IF NOT EXISTS lecture (
    host_id                  INTEGER,
    FOREIGN KEY (host_id) REFERENCES host(host_id),
    path                     TEXT,
    FOREIGN KEY (host_id, path) REFERENCES tutorial(host_id, path),
    lecture_name             TEXT,
    PRIMARY KEY (host_id, path, lecture_name),

    title                    TEXT,

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  lecture IS 'Lectures sit within a tutorial';


CREATE TABLE IF NOT EXISTS stage (
    host_id                  INTEGER,
    path                     TEXT,
    lecture_name             TEXT,
    FOREIGN KEY (host_id, path, lecture_name) REFERENCES lecture(host_id, path, lecture_name),
    stage_name               TEXT,
    version                  INTEGER,
    PRIMARY KEY (host_id, path, lecture_name, stage_name, version),

    stage_id                 SERIAL,
    UNIQUE (stage_id),

    title                    TEXT NOT NULL,
    stage_setting_spec       JSONB,
    material_tags            TEXT[] NOT NULL DEFAULT '{}',

    next_version             INTEGER NULL,
    FOREIGN KEY (host_id, path, lecture_name, stage_name, next_version)
        REFERENCES stage(host_id, path, lecture_name, stage_name, version),

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  stage IS 'An individual stage in this lecture, and the tags for relevant content within';
COMMENT ON COLUMN stage.stage_id IS 'A shorthand to avoid refering to the entire compound key';
COMMENT ON COLUMN stage.stage_setting_spec IS 'dict of setting key to a combination of:'
    '* value: Fixed value / mean value for gamma distribution'
    '* shape: Shape of gamma curve, if set will choose value for each student from gamma curve'
    '* max: Maximum value, if set will choose value between [0, value_max)'
    '* min: Minimum value, applies a lower bound to anything chosen by max'
    '...or "variant:registered", and another set of values below it'
    '...or "deleted", if this stage is now removed';
COMMENT ON COLUMN stage.next_version IS 'If this stage has been replaced by a new version, this field is non-null';


CREATE TABLE IF NOT EXISTS stage_setting (
    stage_id                 INTEGER NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    user_id                  INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id),
    key                      TEXT,
    PRIMARY KEY (stage_id, user_id, key),

    value                    TEXT,

    lastUpdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  stage_setting IS 'All chosen settings for a stage, generic and per-student';
COMMENT ON COLUMN stage_setting.user_id IS 'Student setting is for, or one of the special students:'
     '"(any)" for any student';


COMMIT;
