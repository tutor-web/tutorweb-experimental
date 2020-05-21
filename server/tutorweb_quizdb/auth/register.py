from tutorweb_quizdb.auth.forms import process_form, RegisterSchema
from tutorweb_quizdb.student.create import create_student


def register(request):
    captured = process_form(request, RegisterSchema)
    if not captured.get('_is_form_data', False):
        return captured

    try:
        create_student(
            request,
            captured['handle'],
            captured['email'],
            must_not_exist=True,
        )
    except Exception as e:
        return process_form(
            request,
            RegisterSchema,
            error="Error: %s" % e)

    return dict(
        render_flash_messages=lambda: "",  # TODO:
        form="<p>Please check your e-mail inbox. You shall get a message with further instructions shortly.</p>",
    )


def includeme(config):
    config.add_view(register, route_name='auth_register_register', renderer='templates/register.mako')
    config.add_route('auth_register_register', '/register')
