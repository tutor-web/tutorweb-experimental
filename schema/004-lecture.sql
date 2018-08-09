BEGIN;


-- TODO: A better name that encompasses dept/tutorial/lecture/class
CREATE EXTENSION IF NOT EXISTS ltree;
CREATE TABLE IF NOT EXISTS lecture (
    lecture_id               SERIAL PRIMARY KEY,

    host_id                  INTEGER NOT NULL,
    FOREIGN KEY (host_id) REFERENCES host(host_id),

    path                     LTREE NOT NULL,
    UNIQUE(host_id, path),
    title                    TEXT NOT NULL,

    requires_group_id        INTEGER NOT NULL DEFAULT get_group_id('accept_terms'),
    FOREIGN KEY (requires_group_id) REFERENCES "group"(group_id),

    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('lecture');
CREATE INDEX IF NOT EXISTS lecture_path ON lecture USING GIST(path);
COMMENT ON TABLE  lecture IS 'Lecture/department/tutorial tree sturcture';
COMMENT ON COLUMN lecture.host_id IS 'The host this lecture is from ()';
COMMENT ON COLUMN lecture.path IS 'Path to lecture in short terms, e.g. math.099.lec001';
COMMENT ON COLUMN lecture.title IS 'Full title visible to student';
COMMENT ON COLUMN lecture.requires_group_id IS 'Group ID student has to have before visible, defaults to accept_terms';


CREATE TABLE IF NOT EXISTS stage (
    stage_id                 SERIAL PRIMARY KEY,

    lecture_id               INTEGER NOT NULL,
    FOREIGN KEY (lecture_id) REFERENCES lecture(lecture_id),
    stage_name               TEXT NOT NULL,
    version                  INTEGER,
    UNIQUE (lecture_id, stage_name, version),

    title                    TEXT NOT NULL,
    stage_setting_spec       JSONB,
    material_tags            TEXT[] NOT NULL DEFAULT '{}',  -- TODO: JSONB it?

    next_version             INTEGER NULL,
    FOREIGN KEY (next_version) REFERENCES stage(stage_id),

    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('stage');
COMMENT ON TABLE  stage IS 'An individual stage in this lecture, and the tags for relevant content within';
COMMENT ON COLUMN stage.lecture_id IS 'Lecture this stage is part of';
COMMENT ON COLUMN stage.stage_setting_spec IS 'dict of setting key to a combination of:'
    '* value: Fixed value / mean value for gamma distribution'
    '* shape: Shape of gamma curve, if set will choose value for each student from gamma curve'
    '* max: Maximum value, if set will choose value between [0, value_max)'
    '* min: Minimum value, applies a lower bound to anything chosen by max'
    '...or "variant:registered", and another set of values below it'
    '...or "deleted", if this stage is now removed';
COMMENT ON COLUMN stage.next_version IS 'If this stage has been replaced by a new version, this field is non-null';
CREATE OR REPLACE FUNCTION stage_next_version_insert_fn() RETURNS TRIGGER AS $$
BEGIN
   IF NOT EXISTS(SELECT * FROM stage WHERE lecture_id = NEW.lecture_id AND stage_name = NEW.stage_name) THEN
       -- It's not there, version should be 1.
       NEW.version := 1;
       NEW.next_version := NULL;
       RETURN NEW;
   END IF;
   -- Otherwise, update the existing entry and bump version
   NEW.version := MAX(version) + 1 FROM stage WHERE lecture_id = NEW.lecture_id AND stage_name = NEW.stage_name;
   NEW.stage_id = NEXTVAL(pg_get_serial_sequence('stage', 'stage_id'));
   UPDATE stage SET next_version = NEW.stage_id
       WHERE lecture_id = NEW.lecture_id
       AND stage_name = NEW.stage_name
       AND next_version = NULL;
   RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
DROP TRIGGER IF EXISTS stage_next_version_insert on stage;
CREATE TRIGGER stage_next_version_insert BEFORE INSERT ON stage FOR EACH ROW EXECUTE PROCEDURE stage_next_version_insert_fn();



CREATE TABLE IF NOT EXISTS stage_setting (
    stage_id                 INTEGER NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    user_id                  INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id),
    key                      TEXT,
    PRIMARY KEY (stage_id, user_id, key),

    value                    TEXT,

    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('stage_setting');
COMMENT ON TABLE  stage_setting IS 'All chosen settings for a stage, generic and per-student';
COMMENT ON COLUMN stage_setting.user_id IS 'Student setting is for, or one of the special students:'
     '"(any)" for any student';


CREATE TABLE IF NOT EXISTS subscription (
    user_id                  INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id),
    lecture_id               INTEGER NOT NULL,
    FOREIGN KEY (lecture_id) REFERENCES lecture(lecture_id),
    PRIMARY KEY (user_id, lecture_id),

    hidden                   BOOLEAN NOT NULL DEFAULT 'f',
    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('subscription');
COMMENT ON TABLE  subscription IS 'Student<->tutorial subscriptions';
COMMENT ON COLUMN subscription.hidden IS 'Hide this from the student''s main menu';  -- TODO: Really necessary now?


COMMIT;
