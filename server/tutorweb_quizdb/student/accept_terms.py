from pyramid.httpexceptions import HTTPForbidden

from tutorweb_quizdb import DBSession
from tutorweb_quizdb.student import get_group


def view_student_accept_terms(request):
    """
    We the student accept tutorweb terms
    """
    if not request.user:
        raise HTTPForbidden()

    request.user.add_group(get_group('accept_terms'))
    DBSession.flush()

    return dict(
        success=True,
    )


def includeme(config):
    config.add_view(view_student_accept_terms, route_name='student_accept_terms', renderer='json')
    config.add_route('student_accept_terms', '/student/accept-terms')
