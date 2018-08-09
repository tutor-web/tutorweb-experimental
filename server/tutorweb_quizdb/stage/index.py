import time
import urllib.parse

from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
from tutorweb_quizdb.material.render import material_render
from tutorweb_quizdb.student import get_current_student
from tutorweb_quizdb.rst import to_rst
from .allocation import get_allocation
from .answer_queue import sync_answer_queue
from .setting import getStudentSettings, clientside_settings


def stage_get(host_id, path):
    """
    Get the stage object, given a complete path
    """
    if path.startswith('/api/stage'):
        # Given a URL instead of a path, due to older client code. Unpack the path within
        path = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)['path'][0]
    path = Ltree(path)

    return (DBSession.query(Base.classes.stage)
            .filter_by(stage_name=str(path[-1]))
            .filter_by(next_version=None)
            .join(Base.classes.lecture)
            .filter(Base.classes.lecture.host_id == host_id)
            .filter(Base.classes.lecture.path == path[:-1])
            .one())


def stage_index(request):
    """
    Get all details for a stage
    """
    db_stage = stage_get(ACTIVE_HOST, request.params['path'])
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)

    # Parse incoming JSON body
    incoming = request.json_body if request.body else {}

    # Work out how far off client clock is to ours, to nearest 10s (we're interested in clock-setting issues, request-timing)
    time_offset = round(time.time() - incoming.get('current_time'), -2)

    # Sync answer queue
    (answer_queue, additions) = sync_answer_queue(alloc, incoming.get('answerQueue', []), time_offset)

    # If we've gone over a refresh interval, tell client to throw away questions
    if alloc.should_refresh_questions(answer_queue, additions):
        requested_material = []
    else:
        requested_material = (alloc.from_public_id(x['uri']) for x in incoming.get('questions', []))

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
    db_stage = stage_get(ACTIVE_HOST, request.params['path'])
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
    def format_review(user_id, reviewer_user_id, review):
        """Format incoming review object from stage_ugmaterial"""
        if not review:
            return {}
        review['is_self'] = user_id == reviewer_user_id

        # rst-ize comments
        if review.get('comments', None):
            review['comments'] = to_rst(review['comments'])
        return review

    db_stage = stage_get(ACTIVE_HOST, request.params['path'])
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)

    out = []
    # For all questions that we wrote...
    for (mss_id, permutation, obj, reviews) in DBSession.execute(
            "SELECT material_source_id, permutation, student_answer, reviews FROM stage_ugmaterial"
            " WHERE stage_id = :stage_id"
            "   AND user_id = :user_id"
            " ORDER BY time_end",
            dict(
                stage_id=db_stage.stage_id,
                user_id=alloc.db_student.id,
            )):

        score = len(reviews)  # TODO: Better scoring

        out.append(dict(
            uri=alloc.to_public_id(mss_id, permutation),
            text=to_rst(obj.get('text', '')),
            children=[format_review(alloc.db_student.id, *r) for r in reviews],
            score=score,
        ))
    return dict(material=out)


def stage_request_review(request):
    """
    Request to review some material for this allocation, assuming alloc has
    template questions

    params:
    - path: Stage path
    """
    db_stage = stage_get(ACTIVE_HOST, request.params['path'])
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)

    # Find a question that needs a review
    # Get all questions that we didn't write, ones with least reviews first
    for (mss_id, permutation, reviews) in DBSession.execute(
            "SELECT material_source_id, permutation, reviews FROM stage_ugmaterial"
            " WHERE stage_id = :stage_id"
            "   AND user_id != :user_id"
            " ORDER BY JSONB_ARRAY_LENGTH(reviews), RANDOM()",
            dict(
                stage_id=db_stage.stage_id,
                user_id=alloc.db_student.id,
            )):

        # Consider all reviews
        score = 0
        for (r_user_id, r_obj) in reviews:
            if r_obj is None:
                # Ignore empty reviews
                continue
            if r_user_id == alloc.db_student.id:
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
