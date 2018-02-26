BEGIN;


-- Answers
CREATE TABLE IF NOT EXISTS answer (
    answerId                 UUID PRIMARY KEY,

    lectureStageId           INTEGER NOT NULL,
    studentId                INTEGER NOT NULL DEFAULT 0,
    materialSourceId         SERIAL,
    timeStart                TIMESTAMP WITH TIME ZONE,
    timeEnd                  TIMESTAMP WITH TIME ZONE,

    correct                  BOOLEAN NULL,
    grade                    NUMERIC(4, 3) NOT NULL,
    coinsAwarded             INTEGER NOT NULL DEFAULT 0,

    detail                   JSONB
);


COMMIT;
