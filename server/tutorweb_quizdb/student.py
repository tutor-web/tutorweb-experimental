from pyramid.httpexceptions import HTTPForbidden


def get_current_student(request):
    if not request.user:
        raise HTTPForbidden()
    return request.user


def student_details(request):
    # TODO: This route should also be capable of updating a student
    student = get_current_student(request)

    return student


def includeme(config):
    config.add_view(student_details, route_name='student_details', renderer='json')
    config.add_route('student_details', '/student/details')
