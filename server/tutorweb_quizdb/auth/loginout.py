import datetime

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget, unauthenticated_userid
from sqlalchemy import func

from tutorweb_quizdb import DBSession, models
from tutorweb_quizdb.auth.forms import process_form, LoginSchema


def get_user(request):
    id = unauthenticated_userid(request)
    if id:
        return DBSession.query(models.User).get(id)
    else:
        return None


def login(request):
    if request.method == 'GET' and request.user:
        # Already logged in, skip
        return HTTPFound(location=request.params.get('next') or '/')

    captured = process_form(request, LoginSchema, buttons=('Log_in',))
    if not captured.get('_is_form_data', False):
        return captured

    # Find matching user
    handle = captured['handle'].lower()
    if '@' in handle:
        user = DBSession.query(models.User).filter(
            func.lower(models.User.email) == handle).first()
    else:
        user = DBSession.query(models.User).filter(
            func.lower(models.User.username) == handle).first()

    # Are they valid?
    if not user or not user.check_password(captured['password']):
        return process_form(request, LoginSchema, buttons=('Log_in',), error="Invalid username / password")
    if not user.is_activated:
        return process_form(request, LoginSchema, buttons=('Log_in',), error="Inactive account")

    # Finish login
    user.last_login_date = datetime.datetime.utcnow()
    return HTTPFound(
        headers=remember(request, user.id),
        location=request.params.get('next') or '/',
    )


def logout(request):
    request.session.invalidate()
    return HTTPFound(
        location='/',
        headers=forget(request),
    )


def includeme(config):
    config.add_request_method(get_user, 'user', reify=True)  # populate request.user
    config.add_view(login, route_name='auth_loginout_login', renderer='templates/login.mako')
    config.add_route('auth_loginout_login', '/login')
    config.add_view(logout, route_name='auth_loginout_logout')
    config.add_route('auth_loginout_logout', '/logout')
