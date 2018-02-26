-- Material bank representation
-- Material: question / example/proof / etc.
BEGIN;


CREATE TABLE IF NOT EXISTS dataFrame (
    dataFrameId              SERIAL,
    PRIMARY KEY (dataFrameId),

    path                     TEXT NOT NULL,
    revision                 CHAR(40) NOT NULL,
    UNIQUE (path, revision),

    nextRevision         CHAR(40)
);
COMMENT ON TABLE  dataFrame IS 'material repository source for data frame definitions';


CREATE TABLE IF NOT EXISTS materialSource (
    materialSourceId         SERIAL PRIMARY KEY,

    path                     TEXT NOT NULL,
    revision                 CHAR(40) NOT NULL,
    UNIQUE (path, revision),

    materialTags             TEXT[] NOT NULL DEFAULT '{}',
    dataFrameIds             TEXT[] NOT NULL DEFAULT '{}',
    -- NB: Can't have a FOREIGN KEY on array types

    nextRevision         CHAR(40)
);
COMMENT ON TABLE  materialSource IS 'Source for material, i.e. a file in the material repository';
COMMENT ON COLUMN materialSource.path     IS 'Path to material file';
COMMENT ON COLUMN materialSource.revision IS 'Git revision of this material source';
COMMENT ON COLUMN materialSource.nextRevision IS
    'Next Git revision of this material, i.e. don''t use this one. Deleted material sources get tagged ''deleted''';
--TODO: Default "type:question", "type:example" tags
--TODO: view that gets all unique materialTags
--TODO: Index materialTags
--TODO: Constrain materialTags to something structured?

-- User-generated materials are stored separately 
CREATE TABLE IF NOT EXISTS ugmaterial (
    materialTags             TEXT[] NOT NULL DEFAULT '{}'
);


COMMIT;
