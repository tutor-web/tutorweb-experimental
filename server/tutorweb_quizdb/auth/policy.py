from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import SignedCookieSessionFactory, JSONSerializer

from tutorweb_quizdb import DBSession, models


def read_machine_id():
    """
    Get contents of /etc/machine-id
    """
    with open('/etc/machine-id', 'r') as f:
        return f.read()


def get_user(request):
    id = request.unauthenticated_userid
    if id:
        return DBSession.query(models.User).get(id)
    else:
        return None


def includeme(config):
    machine_id = read_machine_id()
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(AuthTktAuthenticationPolicy(machine_id + '-auth'))
    config.set_session_factory(SignedCookieSessionFactory(machine_id + '-session', serializer=JSONSerializer()))
    config.add_request_method(get_user, 'user', reify=True)  # populate request.user on request
