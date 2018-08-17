from sqlalchemy.orm.exc import NoResultFound

from pyramid.httpexceptions import HTTPForbidden

from tutorweb_quizdb import DBSession, models


def get_group(group_name, auto_create=False):
    """
    Get / create given group
    """
    try:
        g = DBSession.query(models.Group).filter_by(name=group_name).one()
    except NoResultFound:
        if not auto_create:
            raise
        g = models.Group(name=group_name)
        DBSession.add(g)
        DBSession.flush()
    return g


def get_current_student(request):
    if not request.user:
        raise HTTPForbidden()

    if get_group('accept_terms') not in request.user.groups:
        raise HTTPForbidden("User has not accepted terms")

    return request.user


def includeme(config):
    config.include('tutorweb_quizdb.student.details')
    config.include('tutorweb_quizdb.student.accept_terms')
