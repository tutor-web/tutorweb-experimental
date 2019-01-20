import json

from zope.sqlalchemy import mark_changed

from tutorweb_quizdb import DBSession, Base
from ..material.utils import material_bank_open
from .index import alloc_for_view


def dataframe_template(material_bank, path):
    """Fetch the template of given dataframe"""
    with material_bank_open(material_bank, path, 'r') as f:
        return json.load(f)


def view_stage_dataframe(request):
    """
    Get definitions of all dataframes used by stage's questions
    """
    alloc = alloc_for_view(request)
    session = None
    new_data = request.json.data if request.method == 'PUT' else {}

    out = dict()
    for (bank, dataframe_path) in DBSession.execute("""
SELECT DISTINCT bank, UNNEST(dataframe_paths) dataframe_path
  FROM material_source ms
 WHERE material_source_id IN (SELECT material_source_id FROM stage_material WHERE stage_id = :stage_id);
    """, dict(
        user_id=alloc.db_student.user_id,
        stage_id=alloc.db_stage.stage_id,
    )):
        public_name = '%s:%s' % (bank, dataframe_path)  # hashlib.md5(('%s:%s' % (bank, dataframe_path)).encode('utf8')).hexdigest()

        # Fetch JSON for dataframe from material bank
        out[public_name] = dict(
            template=dataframe_template(bank, dataframe_path),
        )

        # Do we have data to insert for this dataframe?
        if public_name in new_data:
            if not session:
                session = DBSession()  # Get a real session, not just a sessionmaker factory, so we can mark_changed
                mark_changed(session)  # Mark this session changed, so sqlalchemy commits
            session.execute("""
                INSERT INTO student_dataframe (user_id, bank, dataframe_path, data)
                     VALUES (:user_id, :bank, :dataframe_path, :data)
                ON CONFLICT (user_id, bank, dataframe_path) DO UPDATE
                        SET data = EXCLUDED.data;
            """, dict(
                user_id=alloc.db_student.user_id,
                bank=bank,
                dataframe_path=dataframe_path,
                data=json.dumps(new_data[public_name]),
            ))
            out[public_name]['data'] = new_data[public_name]
        else:
            out[public_name]['data'] = DBSession.query(Base.classes.student_dataframe.data).filter_by(
                user_id=alloc.db_student.user_id,
                bank=bank,
                dataframe_path=dataframe_path,
            ).one_or_none()
            if out[public_name]['data']:
                out[public_name]['data'] = out[public_name]['data'][0]
    return out


def includeme(config):
    config.add_view(view_stage_dataframe, route_name='stage_dataframe', renderer='json')
    config.add_route('stage_dataframe', '/stage/dataframe')
