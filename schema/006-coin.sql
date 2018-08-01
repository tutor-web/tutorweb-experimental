BEGIN;


CREATE TABLE IF NOT EXISTS coin_award (
    coin_award_id                SERIAL PRIMARY KEY,

    user_id                  INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id),

    amount                   BIGINT NOT NULL,
    wallet                   VARCHAR(100) NOT NULL,
    tx                       VARCHAR(100) NOT NULL,
    award_time               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON COLUMN coin_award.amount IS 'Amount reclaimed, in milliSMLY';

COMMIT;
