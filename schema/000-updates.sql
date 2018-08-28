BEGIN;

-- requires_group_id changed to NULL, we don't specify accept_terms here
DO
$do$
BEGIN
   IF EXISTS (SELECT *
                FROM information_schema.columns
               WHERE table_schema = 'public'
                 AND table_name = 'syllabus'
                 AND column_name = 'requires_group_id'
                 AND is_nullable = 'NO') THEN
       ALTER TABLE syllabus
           ALTER COLUMN requires_group_id DROP DEFAULT,
           ALTER COLUMN requires_group_id DROP NOT NULL;
       UPDATE syllabus
          SET requires_group_id = NULL
        WHERE requires_group_id = get_group_id('accept_terms');
   END IF;
END
$do$;


COMMIT;
