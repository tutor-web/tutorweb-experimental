from pyramid.httpexceptions import HTTPFound

from tutorweb_quizdb.student import get_current_student

from tutorweb_quizdb.auth.forms import process_form, ProfileSchema, user_to_data


def profile_edit(request):
    user = get_current_student(request)

    def process_data(captured):
        user.email = captured['email']
        return HTTPFound(location=request.params.get('next') or '/')

    return process_form(request, ProfileSchema, process_data, init_data=user_to_data(user))


def includeme(config):
    config.add_view(profile_edit, route_name='auth_profile_edit', renderer='templates/profile_edit.mako')
    config.add_route('auth_profile_edit', '/edit_profile')
