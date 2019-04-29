import urllib.parse

from tutorweb_quizdb import DBSession
from sqlalchemy_utils import Ltree


def stage_url(path=None, syllabus_path=None, stage_name=None, stage_id=None):
    if path:
        pass  # Already have a path, nothing to do
    elif stage_id:
        path = DBSession.execute(
            """
            SELECT CONCAT((SELECT sy.path FROM syllabus sy WHERE sy.syllabus_id = st.syllabus_id), '.', st.stage_name) stage_path
              FROM stage st
             WHERE stage_id = :stage_id
            """, dict(
                stage_id=stage_id,
            )).fetchone()
    elif syllabus_path and stage_name:
        path = str(syllabus_path + Ltree(stage_name))
    else:
        raise ValueError("You must pass either path, stage_id or syllabus_path/stage_name")

    return '/api/stage?%s' % urllib.parse.urlencode(dict(path=path))
