import git
import os
import re

import rpy2
import rpy2.robjects as robjects

from pyramid.view import view_config

from tutorweb_quizdb import DBSession, Base


def get_current_student(request):
    # TODO: Hack in me
    return (DBSession.query(Base.classes.user)
        .filter_by(hostdomain=request.registry.settings['tutorweb.host_domain'])
        .filter_by(username='lentinj')
        .one())


def student_details(request):
    # TODO: This route should also be capable of updating a student
    student = get_current_student(request)

    return student


def includeme(config):
    config.add_view(student_details, route_name='student_details', renderer='json')
    config.add_route('student_details', '/student/details')
