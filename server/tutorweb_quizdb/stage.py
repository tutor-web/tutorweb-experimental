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

    return dict(
        uri='/api/stage?%s' % urllib.parse.urlencode(dict(
            path=request.params['path'],
        )),
        user=db_student.username,
        title=db_stage.title,
        settings=dict((k, v) for k, v in settings.items() if k not in SERVERSIDE_SETTINGS),
        questions=[],
        answerQueue=[],
    )


def includeme(config):
    config.add_view(stage_index, route_name='stage_index', renderer='json')
    config.add_route('stage_index', '/stage')
    config.add_route('stage_question', '/stage/question')
