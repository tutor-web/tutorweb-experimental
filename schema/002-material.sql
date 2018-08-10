-- Material bank representation
-- Material: question / example/proof / etc.
BEGIN;


CREATE TABLE IF NOT EXISTS dataframe (
    path                     TEXT NOT NULL,
    revision                 CHAR(40) NOT NULL,
    PRIMARY KEY (path, revision),

    next_revision         CHAR(40)
);
COMMENT ON TABLE  dataframe IS 'material repository source for data frame definitions';


CREATE TABLE IF NOT EXISTS material_source (
    material_source_id       SERIAL PRIMARY KEY,

    bank                     TEXT NOT NULL,
    path                     TEXT NOT NULL,
    revision                 TEXT NOT NULL,
    UNIQUE (bank, path, revision),

    md5sum                   TEXT,
    permutation_count        INTEGER NOT NULL DEFAULT 1,
    material_tags            TEXT[] NOT NULL DEFAULT '{}',
    dataframe_paths          TEXT[] NOT NULL DEFAULT '{}',
    -- NB: Can't have a FOREIGN KEY on array types

    next_revision            TEXT
);
CREATE INDEX IF NOT EXISTS material_source_material_tags ON material_source USING GIN (material_tags);
COMMENT ON TABLE  material_source IS 'Source for material, i.e. a file in the material repository';
COMMENT ON COLUMN material_source.path     IS 'Path to material file';
COMMENT ON COLUMN material_source.revision IS 'Git revision of this material source';
COMMENT ON COLUMN material_source.md5sum   IS 'MD5sum of this version';
COMMENT ON COLUMN material_source.permutation_count IS 'Number of question permutations';
COMMENT ON COLUMN material_source.next_revision IS
    'Next Git revision of this material, i.e. don''t use this one. Deleted material sources get tagged ''deleted''';


CREATE OR REPLACE VIEW all_material_tags AS
    SELECT DISTINCT UNNEST(material_tags) FROM material_source;
COMMENT ON VIEW all_material_tags IS 'All currently used material_tags';


-- User-generated materials are stored separately 
CREATE TABLE IF NOT EXISTS ugmaterial (
    material_tags            TEXT[] NOT NULL DEFAULT '{}'
);


COMMIT;
