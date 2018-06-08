import os
import urllib.parse

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.material.render import material_render
from tutorweb_quizdb.student import get_current_student
from .allocation import get_allocation
from .setting import getStudentSettings, clientside_settings


def stage_get(host_domain, path):
    """
    Get the stage object, given a complete path
    """
    path, stage_name = os.path.split(path)
    path, lecture_name = os.path.split(path)
    return (DBSession.query(Base.classes.stage)
            .filter_by(hostdomain=host_domain)
            .filter_by(path=path)
            .filter_by(lecture_name=lecture_name)
            .filter_by(stage_name=stage_name)
            .filter_by(next_version=None)
            .one())


def stage_index(request):
    """
    Get all details for a stage
    """
    db_stage = stage_get(request.registry.settings['tutorweb.host_domain'], request.params['path'])
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)

    return dict(
        uri='/api/stage?%s' % urllib.parse.urlencode(dict(
            path=request.params['path'],
        )),
        user=db_student.username,
        title=db_stage.title,
        settings=clientside_settings(settings),
        material_tags=db_stage.material_tags,
        questions=None, # TODO: alloc.get_stats(getattr(request, 'json_body', {}).get('questions', None)),  # Get stats for what the client thinks is allocated
        answerQueue=[],
    )


def stage_material(request):
    """
    Get one, or all material for a stage
    """
    db_stage = stage_get(request.registry.settings['tutorweb.host_domain'], request.params['path'])
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)

    if (request.params.get('id', None)):
        requested_material = [alloc.from_public_id(request.params[id])]
    else:
        requested_material = alloc.get_material()

    out = {}
    for m in requested_material:
        ms = DBSession.query(Base.classes.material_source).filter_by(
            material_source_id=m[0],
        ).one()
        out[alloc.to_public_id(m[0], m[1])] = material_render(ms, m[1], obsfucate=True)
    return out


def stage_review(request):
    """
    Get all review material for this stage
    """
    # TODO:
    return []


def includeme(config):
    config.add_view(stage_index, route_name='stage_index', renderer='json')
    config.add_view(stage_material, route_name='stage_material', renderer='json')
    config.add_view(stage_review, route_name='stage_review', renderer='json')
    config.add_route('stage_index', '/stage')
    config.add_route('stage_material', '/stage/material')
    config.add_route('stage_review', '/stage/review')
