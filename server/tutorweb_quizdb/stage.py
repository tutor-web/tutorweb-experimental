import git
import os
import re
import urllib.parse

import rpy2
import rpy2.robjects as robjects

from pyramid.view import view_config

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.student import get_current_student


INTEGER_SETTINGS = set((  # These settings have whole-integer values
    'question_cap',
    'award_lecture_answered',
    'award_lecture_aced',
    'award_tutorial_aced',
    'award_templateqn_aced',
    'cap_template_qns',
    'cap_template_qn_reviews',
    'cap_template_qn_nonsense',
    'grade_nmin',
    'grade_nmax',
))
STRING_SETTINGS = set((  # These settings have string values
    'iaa_mode',
    'grade_algorithm',
))
SERVERSIDE_SETTINGS = set((  # These settings have no relevance clientside
    'prob_template_eval',
    'cap_template_qns',
    'cap_template_qn_reviews',
    'question_cap',
    'award_lecture_answered',
))


def stage_get(path):
    """
    Get the stage object, given a complete path
    """
    path, stage_name = os.path.split(path)
    path, lecture_name = os.path.split(path)
    return (DBSession.query(Base.classes.stage)
            .filter_by(hostdomain='ui-tutorweb3.clifford.shuttlethread.com')
            .filter_by(path=path)
            .filter_by(lecture_name=lecture_name)
            .filter_by(stage_name=stage_name)
            .filter_by(next_version=None)
            .one())


def stage_settings(db_stage, db_student):
    """
    Get / create settings for this student
    """
    #TODO:
    return dict()


def stage_index(request):
    """
    Get all details for a stage
    """
    db_stage = stage_get(request.params['path'])
    db_student = get_current_student(request)
    settings = stage_settings(db_stage, db_student)

    # TODO: Hard-code question bank for now
    if db_stage.stage_name == '0examples':
        questions = [
            dict(path='math099/Q-0990t0/lec050500/QgenFracNoText.e.R', permutation=1),
        ]
    else:
        questions = [
            dict(path='math099/Q-0990t0/lec050500/QgenFracNoText.q.R', permutation=1),
        ]

    return dict(
        uri='/api/stage?%s' % urllib.parse.urlencode(dict(
            path=request.params['path'],
        )),
        user=db_student.username,
        title=db_stage.title,
        settings=dict((k, v) for k, v in settings.items() if k not in SERVERSIDE_SETTINGS),
        material_tags=db_stage.material_tags,
        questions=[dict(uri='/api/material/render?%s' % urllib.parse.urlencode(x)) for x in questions],
        answerQueue=[],
    )


def stage_question(request):
    """
    Get one, or all questions for a stage
    """
    # TODO:
    return {}


def stage_review(request):
    """
    Get all review material for this stage
    """
    # TODO:
    return []


def includeme(config):
    config.add_view(stage_index, route_name='stage_index', renderer='json')
    config.add_view(stage_question, route_name='stage_question', renderer='json')
    config.add_view(stage_review, route_name='stage_review', renderer='json')
    config.add_route('stage_index', '/stage')
    config.add_route('stage_question', '/stage/question')
    config.add_route('stage_review', '/stage/review')
