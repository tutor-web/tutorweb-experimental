import urllib.parse

from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
from tutorweb_quizdb.syllabus import path_to_ltree


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


def get_current_stage(request, optional=False):
    """
    Given a request, find the stage object matching it's querystring
    If optional, then return None if querystring options aren't there. An invalid path is still an error
    """
    if optional and 'path' not in request.params:
        return None
    path = path_to_ltree(request.params['path'])

    return (DBSession.query(Base.classes.stage)
            .filter_by(stage_name=str(path[-1]))
            .filter_by(next_stage_id=None)
            .join(Base.classes.syllabus)
            .filter(Base.classes.syllabus.host_id == ACTIVE_HOST)
            .filter(Base.classes.syllabus.path == path[:-1])
            .one())
