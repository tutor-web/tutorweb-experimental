-- We have mutiple hosts so we can merge data from remote servers
BEGIN;


CREATE TABLE IF NOT EXISTS host (
    host_domain	             TEXT,
    PRIMARY KEY (host_domain),

    host_key	             CHAR(32) NOT NULL
);
COMMENT ON TABLE  host IS 'All known hosts for tutor-web data';
COMMENT ON COLUMN host.host_domain IS 'Fully-qualified domain name';
COMMENT ON COLUMN host.host_key IS 'Secret key for host''s data';


COMMIT;
