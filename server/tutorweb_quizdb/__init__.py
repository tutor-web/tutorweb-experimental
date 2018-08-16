import datetime
import os.path

import pyramid.httpexceptions as exc
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.interfaces import IRendererFactory
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import Ltree
from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.session import SignedCookieSessionFactory

from tutorweb_quizdb import smileycoin


ACTIVE_HOST = 1  # The first host should be "us"


class BaseExtensions(object):
    def __json__(self, request):
        """
        All DB objects should be JSON-serializable

        http://codelike.com/blog/2015/07/19/how-to-serialize-sqlalchemy-objects-to-json-in-pyramid/
        """
        json_exclude = getattr(self, '__json_exclude__', set())
        return {key: value for key, value in self.__dict__.items()
                # Do not serialize 'private' attributes
                # (SQLAlchemy-internal attributes are among those, too)
                if not key.startswith('_') and
                key not in json_exclude}


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = automap_base(cls=BaseExtensions)
import tutorweb_quizdb.models  # noqa
from sqlalchemy_utils import LtreeType  # noqa


def read_machine_id():
    """
    Get contents of /etc/machine-id
    """
    with open('/etc/machine-id', 'r') as f:
        return f.read()


def initialize_dbsession(db_url):
    """
    Use Automap to generate class definitions from tables
    """
    engine = create_engine(db_url)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.prepare(engine, reflect=True)


def index(request):
    """Redirect pluserable from /api to js-controlled /"""
    raise exc.HTTPFound("/")


def main(global_config, **settings):
    """
    Generate WSGI application
    """
    config = Configurator(settings=settings, route_prefix='/api/')

    initialize_dbsession(global_config['ENV_DB_URL'])
    config.set_authorization_policy(ACLAuthorizationPolicy())

    machine_id = read_machine_id()
    config.set_authentication_policy(AuthTktAuthenticationPolicy(machine_id + '-auth'))
    config.set_session_factory(SignedCookieSessionFactory(machine_id + '-session'))
    config.include('pyramid_jinja2')
    config.include('pyramid_mailer')
    config.include('pyramid_mako')

    config.include('pluserable')
    for template in ['login', 'register', 'forgot_password', 'reset_password', 'profile']:
        config.override_asset(
            to_override='pluserable:templates/%s.mako' % template,
            override_with='tutorweb_quizdb:templates/auth/%s.mako' % template
        )
    config.setup_pluserable(os.path.join(global_config['here'], 'kerno.ini'))

    smileycoin.configure(global_config, prefix='ENV_APP_SMILEYCOIN_')

    config.include('tutorweb_quizdb.coin')
    config.include('tutorweb_quizdb.exceptions')
    config.include('tutorweb_quizdb.logerror')
    config.include('tutorweb_quizdb.material.render')
    config.include('tutorweb_quizdb.material.update')
    config.include('tutorweb_quizdb.subscriptions.index')
    config.include('tutorweb_quizdb.stage')
    config.include('tutorweb_quizdb.student')
    config.include('tutorweb_quizdb.rst')

    json_renderer = config.registry.getUtility(IRendererFactory, name="json")
    json_renderer.add_adapter(datetime.datetime, lambda obj, request: obj.isoformat())
    json_renderer.add_adapter(Ltree, lambda obj, request: str(obj))

    config.add_view(index, route_name='index', renderer='json')
    config.add_route('index', '')

    return config.make_wsgi_app()
