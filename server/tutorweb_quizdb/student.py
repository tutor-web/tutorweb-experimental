from pyramid.httpexceptions import HTTPForbidden

from tutorweb_quizdb import DBSession
from tutorweb_quizdb import models


def accept_terms_group():
    return DBSession.query(models.Group).filter_by(name='accept_terms').one()


def get_current_student(request):
    if not request.user:
        raise HTTPForbidden()

    if accept_terms_group() not in request.user.groups:
        raise HTTPForbidden("User has not accepted terms")

    return request.user


def student_accept_terms(request):
    """
    We the student accept tutorweb terms
    """
    if not request.user:
        raise HTTPForbidden()

    if accept_terms_group() not in request.user.groups:
        request.user.groups.append(accept_terms_group())
    DBSession.flush()

    return dict(
        success=True,
    )


def student_details(request):
    if not request.user:
        raise HTTPForbidden()

    rs = DBSession.execute(
        'SELECT balance'
        ' FROM coin_unclaimed'
        ' WHERE user_id = :user_id'
        '', dict(
            user_id=request.user.user_id,
        )
    ).fetchone()

    return dict(
        id=request.user.id,
        email=request.user.email,
        username=request.user.username,
        millismly=int(rs[0]),
    )


def includeme(config):
    config.add_view(student_details, route_name='student_details', renderer='json')
    config.add_view(student_accept_terms, route_name='student_accept_terms', renderer='json')
    config.add_route('student_details', '/student/details')
    config.add_route('student_accept_terms', '/student/accept-terms')
