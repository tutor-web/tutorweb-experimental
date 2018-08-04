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
CREATE INDEX IF NOT EXISTS coin_award_user_id ON coin_award(user_id);  -- For coin_unclaimed view
COMMENT ON COLUMN coin_award.amount IS 'Amount reclaimed, in milliSMLY';


CREATE OR REPLACE VIEW coin_unclaimed AS
    SELECT user_id
         , (SELECT COALESCE(SUM(coins_awarded), 0) FROM answer WHERE user_id = u.user_id)
           - (SELECT COALESCE(SUM(amount), 0) FROM coin_award WHERE user_id = u.user_id) AS balance
      FROM "user" u;
COMMENT ON VIEW coin_unclaimed IS 'Per-user summary of milliSMLY owed to students';


COMMIT;
