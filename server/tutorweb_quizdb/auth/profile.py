from tutorweb_quizdb.student import get_current_student

from tutorweb_quizdb.auth.forms import process_form, ProfileSchema, user_to_data


def edit_profile(request):
    user = get_current_student(request)
    captured = process_form(request, ProfileSchema, init_data=user_to_data(user))
    if not captured.get('_is_form_data', False):
        return captured

    user.email = captured['email']
    return process_form(request, ProfileSchema, init_data=user_to_data(user), error="Your changes have been saved")


def includeme(config):
    config.add_view(edit_profile, route_name='auth_profile_edit', renderer='templates/profile_edit.mako')
    config.add_route('auth_profile_edit', '/edit_profile')
