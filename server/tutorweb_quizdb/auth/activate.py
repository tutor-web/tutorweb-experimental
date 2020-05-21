from pyramid.httpexceptions import HTTPFound

from tutorweb_quizdb.auth.forms import process_form, ActivateRequestSchema, ActivateFinalizeSchema
from tutorweb_quizdb.student.create import activate_trigger_email, activate_set_password


def request_code(request):
    if request.user:
        # Already logged in, so change the current user's password
        email = request.user.email
    else:
        # Not logged in, ask who we should be
        captured = process_form(request, ActivateRequestSchema)
        if not captured.get('_is_form_data', False):
            return captured
        email = captured['email']

    activate_trigger_email(request, email)
    return dict(
        render_flash_messages=lambda: "",
        form="<p>Please check your e-mail inbox. You shall get a message with further instructions shortly.</p>",
    )


def finalize(request):
    code = request.matchdict.get('code', None)
    captured = process_form(request, ActivateFinalizeSchema)
    if not captured.get('_is_form_data', False):
        return captured

    activate_set_password(request, code, captured['password'])
    return HTTPFound(location=request.params.get('next') or '/')


def includeme(config):
    config.add_view(request_code, route_name='auth_activate_request_code', renderer='templates/activate_request_code.mako')
    config.add_route('auth_activate_request_code', '/forgot-password')
    config.add_view(finalize, route_name='auth_activate_finalize', renderer='templates/activate_finalize.mako')
    config.add_route('auth_activate_finalize', '/reset-password/{code}')
