-- Material bank representation
-- Material: question / example/proof / etc.
BEGIN;


CREATE TABLE IF NOT EXISTS dataFrame (
    path                     TEXT NOT NULL,
    revision                 CHAR(40) NOT NULL,
    PRIMARY KEY (path, revision),

    next_revision         CHAR(40)
);
COMMENT ON TABLE  dataFrame IS 'material repository source for data frame definitions';


CREATE TABLE IF NOT EXISTS materialSource (
    materialSourceId         SERIAL PRIMARY KEY,

    path                     TEXT NOT NULL,
    revision                 TEXT NOT NULL,
    UNIQUE (path, revision),

    md5sum                   TEXT,
    permutation_count        INTEGER NOT NULL DEFAULT 1,
    material_tags            TEXT[] NOT NULL DEFAULT '{}',
    dataFrame_paths          TEXT[] NOT NULL DEFAULT '{}',
    -- NB: Can't have a FOREIGN KEY on array types

    next_revision            TEXT
);
COMMENT ON TABLE  materialSource IS 'Source for material, i.e. a file in the material repository';
COMMENT ON COLUMN materialSource.path     IS 'Path to material file';
COMMENT ON COLUMN materialSource.revision IS 'Git revision of this material source';
COMMENT ON COLUMN materialSource.md5sum   IS 'MD5sum of this version';
COMMENT ON COLUMN materialSource.permutation_count IS 'Number of question permutations';
COMMENT ON COLUMN materialSource.next_revision IS
    'Next Git revision of this material, i.e. don''t use this one. Deleted material sources get tagged ''deleted''';
--TODO: Default "type:question", "type:example" tags
--TODO: view that gets all unique material_tags
--TODO: Index material_tags
--TODO: Constrain material_tags to something structured?

-- User-generated materials are stored separately 
CREATE TABLE IF NOT EXISTS ugmaterial (
    material_tags            TEXT[] NOT NULL DEFAULT '{}'
);


COMMIT;
