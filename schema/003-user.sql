-- Users and students
BEGIN;


CREATE TABLE IF NOT EXISTS student (
    hostDomain               TEXT,
    FOREIGN KEY (hostDomain) REFERENCES host(hostDomain),
    userName                 TEXT NOT NULL,
    PRIMARY KEY (hostDomain, userName),
    eMail                    TEXT NULL,

    privileges               TEXT[] NOT NULL DEFAULT '{}'
);
COMMENT ON TABLE  student IS 'All students and administrators';


COMMIT;
