import git
import os
import re

import rpy2
import rpy2.robjects as robjects

from pyramid.view import view_config

from tutorweb_quizdb import DBSession, Base


def student_details(request):
    # TODO: This route should also be capable of updating a student
    # TODO: Hack in me
    student = (DBSession.query(Base.classes.student)
        .filter_by(hostdomain='ui-tutorweb3.clifford.shuttlethread.com')
        .filter_by(username='lentinj')
        .one())

    return student


def includeme(config):
    config.add_view(student_details, route_name='student_details', renderer='json')
    config.add_route('student_details', '/student/details')
