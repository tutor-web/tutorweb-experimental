-- We have mutiple hosts so we can merge data from remote servers
BEGIN;


CREATE TABLE IF NOT EXISTS host (
    host_id                  SERIAL,
    PRIMARY KEY (host_id),

    name	             TEXT NOT NULL,
    key                      UUID NULL
);
COMMENT ON TABLE  host IS 'All known hosts for tutor-web data';
COMMENT ON COLUMN host.name IS 'Friendly name for host, e.g. Fully-qualified domain name';
COMMENT ON COLUMN host.key IS 'Secret key for sharing host''s data';

DO
$$
BEGIN
    IF NOT EXISTS(SELECT * FROM host) THEN
        -- Make sure there's a host_id=1 entry for ourselves
        -- NB: Generating UUIDs requires a postgres extension, so don't bother here. Do it in python when dumping data
        INSERT INTO host (host_id, name, key)
            VALUES (1, '(self)', NULL);
        -- Make sure the sequence has moved off the first value
        PERFORM NEXTVAL(PG_GET_SERIAL_SEQUENCE('host', 'host_id'));
    END IF ;
END;
$$ LANGUAGE 'plpgsql';

COMMIT;
