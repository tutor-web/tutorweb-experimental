BEGIN;


-- Answers
CREATE TABLE IF NOT EXISTS answer (
    answerId                 UUID PRIMARY KEY,

    stage_id                 INTEGER NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    hostDomain               TEXT,
    userName                 TEXT,
    FOREIGN KEY (hostDomain, userName) REFERENCES student(hostDomain, userName),

    materialSourceId         SERIAL,
    timeStart                TIMESTAMP WITH TIME ZONE,
    timeEnd                  TIMESTAMP WITH TIME ZONE,

    correct                  BOOLEAN NULL,
    grade                    NUMERIC(4, 3) NOT NULL,
    coinsAwarded             INTEGER NOT NULL DEFAULT 0,

    detail                   JSONB
);


COMMIT;
