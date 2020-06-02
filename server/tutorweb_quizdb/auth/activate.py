from pyramid.httpexceptions import HTTPFound

from tutorweb_quizdb.auth.forms import process_form, ActivateRequestSchema, ActivateFinalizeSchema
from tutorweb_quizdb.student.create import activate_trigger_email, activate_set_password


def request_code(request):
    def process_data(captured):
        activate_trigger_email(request, captured['email'])
        return dict(
            form="<p>Please check your e-mail inbox. You shall get a message with further instructions shortly.</p>",
        )

    if request.user:
        # Already logged in, so change the current user's password
        return process_data(dict(email=request.user.email))
    return process_form(request, ActivateRequestSchema, process_data)


def finalize(request):
    def process_data(captured):
        code = request.matchdict.get('code', None)
        activate_set_password(request, code, captured['password'])
        return HTTPFound(location=request.params.get('next') or '/')

    return process_form(request, ActivateFinalizeSchema, process_data)


def includeme(config):
    config.add_route('auth_activate_request_code', '/forgot-password')
    config.add_view(request_code, route_name='auth_activate_request_code', renderer='templates/activate_request_code.mako')
    config.add_route('auth_activate_finalize', '/reset-password/{code}')
    config.add_view(finalize, route_name='auth_activate_finalize', renderer='templates/activate_finalize.mako')
