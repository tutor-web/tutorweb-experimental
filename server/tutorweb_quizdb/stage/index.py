import time

from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
from tutorweb_quizdb.stage.utils import stage_url
from tutorweb_quizdb.student import get_current_student
from tutorweb_quizdb.syllabus import path_to_ltree
from .allocation import get_allocation
from .answer_queue import sync_answer_queue
from .setting import getStudentSettings, clientside_settings


def update_stats(alloc, questions):
    """Update answered / correct counts for this question array before sending out"""
    for q, s in zip(questions, alloc.get_stats([x['uri'] for x in questions])):
        q['chosen'] = q['initial_answered'] + s['stage_answered']
        q['correct'] = q['initial_correct'] + s['stage_correct']


def stage_get(host_id, path):
    """
    Get the stage object, given a complete path
    """
    return (DBSession.query(Base.classes.stage)
            .filter_by(stage_name=str(path[-1]))
            .filter_by(next_stage_id=None)
            .join(Base.classes.syllabus)
            .filter(Base.classes.syllabus.host_id == host_id)
            .filter(Base.classes.syllabus.path == path[:-1])
            .one())


def alloc_for_view(request):
    """
    Return a configured allocation object based in request params
    """
    db_stage = stage_get(ACTIVE_HOST, path_to_ltree(request.params['path']))
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    return get_allocation(settings, db_stage, db_student)


def stage_index(request):
    """
    Get all details for a stage
    """
    alloc = alloc_for_view(request)

    # Parse incoming JSON body
    incoming = request.json_body if request.body else {}

    # Work out how far off client clock is to ours, to nearest 10s (we're interested in clock-setting issues, request-timing)
    time_offset = round(time.time() - incoming.get('current_time', time.time()), -2)

    # Sync answer queue
    (answer_queue, additions) = sync_answer_queue(alloc, incoming.get('answerQueue', []), time_offset)

    # If we've gone over a refresh interval, tell client to throw away questions
    if alloc.should_refresh_questions(answer_queue, additions):
        questions = []
    else:
        # Get new stats for each question, update
        questions = incoming.get('questions', [])
        update_stats(alloc, questions)

    return dict(
        uri=stage_url(path=request.params['path']),
        path=request.params['path'],
        user=alloc.db_student.username,
        title=alloc.db_stage.title,
        settings=clientside_settings(alloc.settings),
        material_tags=alloc.db_stage.material_tags,
        questions=questions,
        answerQueue=answer_queue,
        time_offset=time_offset,
    )


def includeme(config):
    config.add_view(stage_index, route_name='stage_index', renderer='json')
    config.add_route('stage_index', '/stage')
