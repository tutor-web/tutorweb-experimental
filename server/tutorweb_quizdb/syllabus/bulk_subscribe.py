from tutorweb_quizdb.student import get_current_student, student_check_group
from tutorweb_quizdb.student.create import create_student
from tutorweb_quizdb.syllabus import path_to_ltree


def view_bulk_subscribe(request):
    student = get_current_student(request)
    path = path_to_ltree(request.params['path'])
    student_check_group(student, 'admin.%s' % path, error="Not an admin")

    out = []
    for new_user in request.json['users']:
        if not isinstance(new_user, list):
            new_user = [new_user]
        (new_user, password) = create_student(
            request,
            new_user[0],
            new_user[1] if len(new_user) > 1 else new_user[0],
            assign_password=bool(request.json.get('assign_password', False)),
            subscribe=[path],
        )

        out.append(dict(
            user_name=new_user.user_name,
            email=new_user.email,
            password=password or '',
        ))

    return dict(
        users=out
    )


def includeme(config):
    config.add_view(view_bulk_subscribe, route_name='syllabus_bulk_subscribe', renderer='json')
    config.add_route('syllabus_bulk_subscribe', '/syllabus/bulk_subscribe', request_method='POST')
