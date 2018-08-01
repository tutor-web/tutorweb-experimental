import datetime

import pyramid.httpexceptions as exc
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.interfaces import IRendererFactory
from sqlalchemy import engine_from_config
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.session import SignedCookieSessionFactory

from tutorweb_quizdb import smileycoin


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
Base = automap_base(declarative_base=declarative_base(cls=BaseExtensions))
import tutorweb_quizdb.models  # noqa


def initialize_dbsession(settings):
    """
    Use Automap to generate class definitions from tables
    """
    engine = engine_from_config(settings, prefix='sqlalchemy.')
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

    tutorweb_quizdb.models.ACTIVE_HOST_DOMAIN = settings['tutorweb.host_domain']
    initialize_dbsession(settings)
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(AuthTktAuthenticationPolicy(settings.get('pyramid_auth.secret', 'itsaseekreet')))
    config.set_session_factory(SignedCookieSessionFactory(settings.get('pyramid_session.secret', 'itsaseekreet')))
    config.include('pyramid_jinja2')
    config.include('pyramid_mailer')
    config.include('pyramid_mako')

    config.include('pluserable')
    for template in ['login', 'register', 'forgot_password', 'reset_password', 'profile']:
        config.override_asset(
            to_override='pluserable:templates/%s.mako' % template,
            override_with='tutorweb_quizdb:templates/auth/%s.mako' % template
        )
    config.setup_pluserable(global_config['__file__'])

    smileycoin.configure(settings, prefix='smileycoin.')

    config.include('tutorweb_quizdb.coin')
    config.include('tutorweb_quizdb.exceptions')
    config.include('tutorweb_quizdb.logerror')
    config.include('tutorweb_quizdb.material.render')
    config.include('tutorweb_quizdb.material.update')
    config.include('tutorweb_quizdb.subscriptions.list')
    config.include('tutorweb_quizdb.stage')
    config.include('tutorweb_quizdb.student')
    config.include('tutorweb_quizdb.rst')

    json_renderer = config.registry.getUtility(IRendererFactory, name="json")
    json_renderer.add_adapter(datetime.datetime, lambda obj, request: obj.isoformat())

    config.add_view(index, route_name='index', renderer='json')
    config.add_route('index', '')

    return config.make_wsgi_app()
