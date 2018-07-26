-- Users and students
BEGIN;


CREATE TABLE IF NOT EXISTS activation (
    activation_id            SERIAL NOT NULL,
    PRIMARY KEY (activation_id),

    code                     VARCHAR(30) NOT NULL,
    UNIQUE (code),
    created_by               VARCHAR(30) NOT NULL,
    valid_until              TIMESTAMP WITHOUT TIME ZONE NOT NULL
);


CREATE TABLE IF NOT EXISTS "user" (
    hostDomain               TEXT,
    FOREIGN KEY (hostDomain) REFERENCES host(hostDomain),
    user_id                  SERIAL,  -- NB: user_id is only unique within a host
    PRIMARY KEY (hostDomain, user_id),

    user_name                TEXT NULL, -- NB: We allow NULL for remote hosts
    email                    TEXT NULL,
    last_login_date          TIMESTAMP NOT NULL DEFAULT now(),
    registered_date          TIMESTAMP NOT NULL DEFAULT now(),
    pw_hash                  VARCHAR(256) NOT NULL,
    salt                     VARCHAR(256) NOT NULL,
    activation_id            INTEGER,
    FOREIGN KEY (activation_id) REFERENCES activation(activation_id)
);
COMMENT ON TABLE  "user" IS 'All students and administrators';
COMMENT ON COLUMN "user".hostDomain IS 'The host this user belongs to';
COMMENT ON COLUMN "user".user_id IS 'Numeric ID for user (unique per-host)';
COMMENT ON COLUMN "user".user_name IS 'Host user name (e.g. "official" e-mail address)';


CREATE TABLE IF NOT EXISTS "group" (
    group_id                 SERIAL NOT NULL,
    PRIMARY KEY (group_id),

    name                     VARCHAR(50),
    UNIQUE (name),

    description              TEXT
);
COMMENT ON TABLE  "group" IS 'All groups';
INSERT INTO "group" (name, description)
    VALUES ('accept_terms', 'Accepted terms and conditions')
    ON CONFLICT (name)
    DO UPDATE SET description = 'Accepted terms and conditions';


CREATE TABLE IF NOT EXISTS user_group (
    user_group_id            SERIAL NOT NULL,
    PRIMARY KEY (user_group_id),

    group_id                 INTEGER,
    hostDomain               TEXT,
    user_id                  INTEGER,
    FOREIGN KEY(group_id) REFERENCES "group" (group_id),
    FOREIGN KEY(hostDomain, user_id) REFERENCES "user"(hostDomain, user_id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE  user_group IS 'Many-to-many user:group';


COMMIT;
