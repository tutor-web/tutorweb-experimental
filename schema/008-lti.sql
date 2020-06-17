BEGIN;


CREATE UNLOGGED TABLE IF NOT EXISTS lti_nonce (
    timestamp INT,
    client_key TEXT,
    nonce TEXT,
    token TEXT,
    PRIMARY KEY (timestamp, client_key, nonce, token)
);
COMMENT ON TABLE  lti_nonce IS 'Temporary authentication nonce storage';
COMMENT ON COLUMN lti_nonce.client_key IS 'OAuth client_key';
COMMENT ON COLUMN lti_nonce.timestamp IS 'OAuth nonce timestamp (i.e when it was made)';
COMMENT ON COLUMN lti_nonce.nonce IS 'OAuth nonce (unique string token to be used once)';


COMMIT;
