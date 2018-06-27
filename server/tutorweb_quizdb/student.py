from pyramid.httpexceptions import HTTPForbidden


def get_current_student(request):
    if not request.user:
        raise HTTPForbidden()
    return request.user


def student_details(request):
    student = get_current_student(request)

    return dict(
        id=student.id,
        email=student.email,
        username=student.username,
        host_domain=student.host_domain,
        smly=25,  # TODO:
    )


def includeme(config):
    config.add_view(student_details, route_name='student_details', renderer='json')
    config.add_route('student_details', '/student/details')
