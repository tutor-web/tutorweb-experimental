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

    student_check_group(request.user, 'accept_terms', error="User has not accepted terms")

    return request.user


def student_check_group(student, group_name, error=None):
    """Is (student) part of (group_name)? Raise HTTPForbidden(error) if (error) given"""
    try:
        group = get_group(group_name, auto_create=False)
    except NoResultFound:
        # No group exists, so student can't be part of it
        group = None

    if group and group in student.groups:
        # Success
        return True

    # If we've got an error to raise, raise it. Otherwise return false
    if error:
        raise HTTPForbidden(error)
    return False


def student_is_vetted(student, stage):
    """Is this student vetted to review this stage in more detail?"""
    # Consider vettings at the tutorial-level
    return student_check_group(student, 'vetted.%s' % stage.syllabus.path[:-1])


def includeme(config):
    config.include('tutorweb_quizdb.student.details')
    config.include('tutorweb_quizdb.student.accept_terms')
    config.include('tutorweb_quizdb.student.create')
