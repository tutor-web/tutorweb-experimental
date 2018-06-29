BEGIN;


-- Answers
CREATE TABLE IF NOT EXISTS answer (
    answer_id                SERIAL PRIMARY KEY,

    stage_id                 INTEGER NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    host_domain               TEXT,
    user_id                  INTEGER,
    FOREIGN KEY (host_domain, user_id) REFERENCES "user"(hostDomain, user_id),

    material_source_id       INTEGER,
    permutation              INTEGER,
    client_id                TEXT NOT NULL,
    time_start               TIMESTAMP WITHOUT TIME ZONE,  -- NB: Always UTC
    time_end                 TIMESTAMP WITHOUT TIME ZONE,  -- NB: Always UTC
    time_offset              INTEGER NOT NULL DEFAULT 0,

    correct                  BOOLEAN NULL,
    grade                    NUMERIC(4, 3) NOT NULL,
    coins_awarded            INTEGER NOT NULL DEFAULT 0,

    student_answer           JSONB,
    review                   JSONB
);
COMMENT ON TABLE  answer IS 'Raw answer objects synced from client';
COMMENT ON COLUMN answer.time_start IS 'When the student started answering, in UTC';
COMMENT ON COLUMN answer.time_end IS 'When the student finished answering, in UTC';
COMMENT ON COLUMN answer.time_offset IS 'Difference between server and client UTC time, to nearest 10s';
COMMENT ON COLUMN answer.coins_awarded IS 'SMLY awarded for this question, in milli-SMLY';
COMMENT ON COLUMN answer.student_answer IS 'The student_answer object, i.e. the raw form selections';
COMMENT ON COLUMN answer.review IS 'The students review of the material, if they did one';


CREATE OR REPLACE VIEW answer_stats AS
    SELECT a.stage_id
         , a.material_source_id
         , COUNT(*) chosen
         , COUNT(a.correct) correct
    FROM answer a
    GROUP BY 1, 2;
COMMENT ON VIEW answer_stats IS 'Answer stats for each stage/material_source combo';


CREATE OR REPLACE VIEW stage_material AS
    SELECT s.stage_id
         , ms.material_source_id
         , GENERATE_SERIES(1, ms.permutation_count) "permutation"
         , COALESCE(stats.chosen, 0) chosen
         , COALESCE(stats.correct, 0) correct
    FROM stage s
    JOIN material_source ms
      ON s.material_tags <@ ms.material_tags
    LEFT JOIN answer_stats stats
           ON ms.material_source_id = stats.material_source_id
          AND s.stage_id = stats.stage_id
    WHERE ms.next_revision IS NULL
      AND s.next_version IS NULL;
COMMENT ON VIEW stage_material IS 'All appropriate material for all stages, and their stats';


COMMIT;
