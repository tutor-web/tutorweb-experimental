from tutorweb_quizdb.auth.forms import process_form, RegisterSchema
from tutorweb_quizdb.student.create import create_student


def register(request):
    def process_data(captured):
        create_student(
            request,
            captured['handle'],
            captured['email'],
            must_not_exist=True,
        )
        return dict(
            form="<p>Please check your e-mail inbox. You shall get a message with further instructions shortly.</p>",
        )
    return process_form(request, RegisterSchema, process_data)


def includeme(config):
    config.add_view(register, route_name='auth_register_register', renderer='templates/register.mako')
    config.add_route('auth_register_register', '/register')
