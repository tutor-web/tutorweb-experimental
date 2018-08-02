BEGIN;


CREATE OR REPLACE FUNCTION update_lastupdate_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.lastupdate = now();
   RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';


-- Helper to create a lastupdate-update trigger if one doesn't already exist
CREATE OR REPLACE FUNCTION ddl_lastupdate_trigger(tbl TEXT)
RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS(SELECT * 
                FROM information_schema.triggers
                WHERE event_object_table = tbl
                AND trigger_name = 'update_' || tbl || '_lastupdate'
                ) THEN
        EXECUTE(
            'CREATE TRIGGER ' || 'update_' || tbl || '_lastupdate' ||
            ' BEFORE UPDATE ON ' || tbl ||
            ' FOR EACH ROW EXECUTE PROCEDURE update_lastupdate_column()');
    END IF ;
END;
$$ LANGUAGE 'plpgsql';

COMMIT;
