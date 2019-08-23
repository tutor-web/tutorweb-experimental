BEGIN;


-- TODO: Do we need to version user data?
CREATE TABLE IF NOT EXISTS student_dataframe (
    user_id                  INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id),
    bank                     TEXT NOT NULL,
    dataframe_path           TEXT NOT NULL,
    PRIMARY KEY (user_id, bank, dataframe_path),
    
    data                     JSONB NOT NULL
);


COMMIT;
