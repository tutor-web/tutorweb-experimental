BEGIN;


-- Answers
CREATE TABLE IF NOT EXISTS answer (
    answerId                 UUID PRIMARY KEY,

    stage_id                 INTEGER NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    hostDomain               TEXT,
    user_id                  INTEGER,
    FOREIGN KEY (hostDomain, user_id) REFERENCES "user"(hostDomain, user_id),

    material_source_id       INTEGER,
    permutation              INTEGER,
    timeStart                TIMESTAMP WITH TIME ZONE,
    timeEnd                  TIMESTAMP WITH TIME ZONE,

    correct                  BOOLEAN NULL,
    grade                    NUMERIC(4, 3) NOT NULL,
    coinsAwarded             INTEGER NOT NULL DEFAULT 0,

    detail                   JSONB
);


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
