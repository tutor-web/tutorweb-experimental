from pyramid.httpexceptions import HTTPForbidden

from tutorweb_quizdb import DBSession


def view_student_details(request):
    if not request.user:
        raise HTTPForbidden()
    # NB: We don't use get_current_student since we don't care about accepted terms

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
    config.add_view(view_student_details, route_name='student_details', renderer='json')
    config.add_route('student_details', '/student/details')
