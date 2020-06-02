import datetime

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget
from sqlalchemy import func

from tutorweb_quizdb import DBSession, models
from tutorweb_quizdb.auth.forms import process_form, LoginSchema


def login(request):
    def process_data(captured):
        # Find matching user
        handle = captured['handle'].lower()
        user = DBSession.query(models.User).filter(
            func.lower(models.User.username) == handle).first()

        # Are they valid?
        if not user or not user.check_password(captured['password']):
            raise ValueError("Invalid username / password")
        if not user.is_activated:
            raise ValueError("Inactive account")

        # Finish login
        user.last_login_date = datetime.datetime.utcnow()
        return HTTPFound(
            headers=remember(request, user.id),
            location=request.params.get('next') or '/',
        )

    if request.method == 'GET' and request.user:
        # Already logged in, skip
        return HTTPFound(location=request.params.get('next') or '/')
    return process_form(request, LoginSchema, process_data)


def logout(request):
    request.session.invalidate()
    return HTTPFound(
        location='/',
        headers=forget(request),
    )


def includeme(config):
    config.add_view(login, route_name='auth_loginout_login', renderer='templates/login.mako')
    config.add_route('auth_loginout_login', '/login')
    config.add_view(logout, route_name='auth_loginout_logout')
    config.add_route('auth_loginout_logout', '/logout')
