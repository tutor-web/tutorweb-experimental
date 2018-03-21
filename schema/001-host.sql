-- We have mutiple hosts so we can merge data from remote servers
BEGIN;


CREATE TABLE IF NOT EXISTS host (
    hostDomain	             TEXT,
    PRIMARY KEY (hostDomain),

    hostKey	             CHAR(32) NOT NULL
);
COMMENT ON TABLE  host IS 'All known hosts for tutor-web data';
COMMENT ON COLUMN host.hostDomain IS 'Fully-qualified domain name';
COMMENT ON COLUMN host.hostKey IS 'Secret key for host''s data';


COMMIT;
