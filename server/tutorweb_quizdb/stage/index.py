import os
import time
import urllib.parse

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.material.render import material_render
from tutorweb_quizdb.student import get_current_student
from .allocation import get_allocation
from .answer_queue import sync_answer_queue
from .setting import getStudentSettings, clientside_settings


def stage_get(host_domain, path):
    """
    Get the stage object, given a complete path
    """
    if path.startswith('/api/stage'):
        # Given a URL instead of a path, due to older client code. Unpack the path within
        path = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)['path'][0]
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

    # Parse incoming JSON body
    incoming = request.json_body if request.body else {}

    # Work out how far off client clock is to ours, to nearest 10s (we're interested in clock-setting issues, request-timing)
    time_offset = round(time.time() - incoming.get('current_time'), -2)

    # Get material IDs that the client thinks are allocated
    requested_material = (alloc.from_public_id(x['uri']) for x in incoming.get('questions', []))

    # Sync answer queue
    answer_queue = sync_answer_queue(alloc, incoming.get('answerQueue', []), time_offset)

    return dict(
        uri='/api/stage?%s' % urllib.parse.urlencode(dict(
            path=request.params['path'],
        )),
        path=request.params['path'],
        user=db_student.username,
        title=db_stage.title,
        settings=clientside_settings(settings),
        material_tags=db_stage.material_tags,
        questions=alloc.get_stats(requested_material),
        answerQueue=answer_queue,
        time_offset=time_offset,
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
        requested_material = [alloc.from_public_id(request.params['id'])]
    else:
        requested_material = alloc.get_material()

    out = dict(
        stats=alloc.get_stats(requested_material),
        data={},
    )
    for m in requested_material:
        ms = DBSession.query(Base.classes.material_source).filter_by(
            material_source_id=m[0],
        ).one()
        out['data'][alloc.to_public_id(m[0], m[1])] = material_render(ms, m[1])
    return out


def stage_review(request):
    """
    Get the reviews for all questions you have written
    """
    # TODO:
    return []


def stage_request_review(request):
    """
    Request to review some material for this allocation, assuming alloc has
    template questions

    params:
    - path: Stage path
    """
    db_stage = stage_get(request.registry.settings['tutorweb.host_domain'], request.params['path'])
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)

    # Find a question that needs a review
    # Get all questions that we didn't write, ones with least reviews first
    for (mss_id, permutation, reviews) in DBSession.execute(
            "SELECT material_source_id, permutation, reviews FROM stage_ugmaterial"
            " WHERE stage_id = :stage_id"
            "   AND (host_domain != :host_domain OR user_id != :user_id)"
            " ORDER BY JSONB_ARRAY_LENGTH(reviews), RANDOM()",
            dict(
                stage_id=db_stage.stage_id,
                host_domain=alloc.db_student.host_domain,
                user_id=alloc.db_student.id,
            )):

        # Consider all reviews
        score = 0
        for (r_host_domain, r_user_id, r_obj) in reviews:
            if r_obj is None:
                # Ignore empty reviews
                continue
            if r_host_domain == alloc.db_student.host_domain and r_user_id == alloc.db_student.id:
                # We reviewed it ourselves, so ignore it
                score = -99
                break
            if r_obj['superseded']:
                # This question has been replaced, ignore it
                score = -99
                break

        if score >= 0:
            # This one is good enough for reviewing
            return dict(uri=alloc.to_public_id(mss_id, permutation))

    # No available material to review
    return dict()


def includeme(config):
    config.add_view(stage_index, route_name='stage_index', renderer='json')
    config.add_view(stage_material, route_name='stage_material', renderer='json')
    config.add_view(stage_review, route_name='stage_review', renderer='json')
    config.add_view(stage_request_review, route_name='stage_request_review', renderer='json')
    config.add_route('stage_index', '/stage')
    config.add_route('stage_material', '/stage/material')
    config.add_route('stage_review', '/stage/review')
    config.add_route('stage_request_review', '/stage/request-review')
