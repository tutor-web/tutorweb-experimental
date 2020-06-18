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


CREATE TABLE IF NOT EXISTS lti_sourcedid (
    user_id                  INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id),
    stage_id                  INTEGER,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    PRIMARY KEY (user_id, stage_id),

    client_key               TEXT NOT NULL,
    lis_outcome_service_url  TEXT NOT NULL,
    lis_result_sourcedid     TEXT NOT NULL,

    last_perc                NUMERIC(5, 4) NULL,
    last_error               TEXT NULL,
    lastupdate               TIMESTAMP NOT NULL DEFAULT NOW()
);
SELECT ddl_lastupdate_trigger('lti_sourcedid');
COMMENT ON TABLE  lti_sourcedid IS 'Where LTI integration should report back to, for a given stage/student';
COMMENT ON COLUMN lti_sourcedid.client_key IS 'OAuth client_key';
COMMENT ON COLUMN lti_sourcedid.lis_outcome_service_url IS 'URL reported by LTI ToolConsumer';
COMMENT ON COLUMN lti_sourcedid.lis_result_sourcedid IS 'ID for assignment in LTI ToolConsumer (i.e. where the grade goes)';
COMMENT ON COLUMN lti_sourcedid.last_perc IS 'Last percentage successfully reported to LTI ToolConsumer';
COMMENT ON COLUMN lti_sourcedid.last_error IS 'Error received from LTI ToolConsumer, or NULL if successful';


COMMIT;
