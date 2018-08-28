BEGIN;


CREATE EXTENSION IF NOT EXISTS ltree;
CREATE TABLE IF NOT EXISTS syllabus (
    syllabus_id              SERIAL PRIMARY KEY,

    host_id                  INTEGER NOT NULL,
    FOREIGN KEY (host_id) REFERENCES host(host_id),

    path                     LTREE NOT NULL,
    UNIQUE(host_id, path),
    title                    TEXT NOT NULL,
    supporting_material_href TEXT NULL,

    requires_group_id        INTEGER NULL,
    FOREIGN KEY (requires_group_id) REFERENCES "group"(group_id),

    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('syllabus');
CREATE INDEX IF NOT EXISTS syllabus_path ON syllabus USING GIST(path);
COMMENT ON TABLE  syllabus IS 'Lecture/department/tutorial tree sturcture';
COMMENT ON COLUMN syllabus.host_id IS 'The host this syllabus item is from ()';
COMMENT ON COLUMN syllabus.path IS 'Path to syllabus item in short name terms, e.g. math.099.lec001';
COMMENT ON COLUMN syllabus.title IS 'Full syllabus item title visible to student';
COMMENT ON COLUMN syllabus.supporting_material_href IS 'URL pointing to, e.g. PDFs of content';
COMMENT ON COLUMN syllabus.requires_group_id IS 'Group ID student has to have before visible, defaults to accept_terms';


CREATE TABLE IF NOT EXISTS stage (
    stage_id                 SERIAL PRIMARY KEY,

    syllabus_id              INTEGER NOT NULL,
    FOREIGN KEY (syllabus_id) REFERENCES syllabus(syllabus_id),
    stage_name               TEXT NOT NULL,
    version                  INTEGER,
    UNIQUE (syllabus_id, stage_name, version),

    title                    TEXT NOT NULL,
    stage_setting_spec       JSONB,
    material_tags            TEXT[] NOT NULL DEFAULT '{}',  -- TODO: JSONB it?

    next_stage_id            INTEGER NULL,
    FOREIGN KEY (next_stage_id) REFERENCES stage(stage_id),

    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('stage');
COMMENT ON TABLE  stage IS 'An individual stage in this syllabus item, and the tags for relevant content within';
COMMENT ON COLUMN stage.syllabus_id IS 'Syllabus item this stage is part of';
COMMENT ON COLUMN stage.stage_setting_spec IS 'dict of setting key to a combination of:'
    '* value: Fixed value / mean value for gamma distribution'
    '* shape: Shape of gamma curve, if set will choose value for each student from gamma curve'
    '* max: Maximum value, if set will choose value between [0, value_max)'
    '* min: Minimum value, applies a lower bound to anything chosen by max'
    '...or "variant:registered", and another set of values below it'
    '...or "deleted", if this stage is now removed';
COMMENT ON COLUMN stage.next_stage_id IS 'The replacement stage_id, or NULL if this field is current';
CREATE OR REPLACE FUNCTION stage_next_stage_id_before_insert_fn() RETURNS TRIGGER AS $$
BEGIN
   NEW.next_stage_id := NULL;
   -- Version should be one greater than the maximum, or start at 1
   NEW.version := COALESCE(MAX(version), 0) + 1 FROM stage WHERE syllabus_id = NEW.syllabus_id AND stage_name = NEW.stage_name;
   RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
DROP TRIGGER IF EXISTS stage_next_stage_id_before_insert on stage;
CREATE TRIGGER stage_next_stage_id_before_insert BEFORE INSERT ON stage FOR EACH ROW EXECUTE PROCEDURE stage_next_stage_id_before_insert_fn();
CREATE OR REPLACE FUNCTION stage_next_stage_id_after_insert_fn() RETURNS TRIGGER AS $$
BEGIN
   -- Any now-old versions should point at us
   UPDATE stage
       SET next_stage_id = NEW.stage_id
       WHERE syllabus_id = NEW.syllabus_id
       AND stage_name = NEW.stage_name
       AND stage_id != NEW.stage_id
       AND next_stage_id IS NULL;
   RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
DROP TRIGGER IF EXISTS stage_next_stage_id_after_insert on stage;
CREATE TRIGGER stage_next_stage_id_after_insert AFTER INSERT ON stage FOR EACH ROW EXECUTE PROCEDURE stage_next_stage_id_after_insert_fn();



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
    syllabus_id              INTEGER NOT NULL,
    FOREIGN KEY (syllabus_id) REFERENCES syllabus(syllabus_id),
    PRIMARY KEY (user_id, syllabus_id),

    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('subscription');
COMMENT ON TABLE  subscription IS 'Student<->syllabus item subscriptions';


COMMIT;
