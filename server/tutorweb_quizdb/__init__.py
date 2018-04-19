from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.session import SignedCookieSessionFactory


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
                if not key.startswith('_')
                and key not in json_exclude}


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = automap_base(declarative_base=declarative_base(cls=BaseExtensions))


def initialize_dbsession(settings):
    """
    Use Automap to generate class definitions from tables
    """
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.prepare(engine, reflect=True)


def main(global_config, **settings):
    """
    Generate WSGI application
    """
    config = Configurator(settings=settings)

    initialize_dbsession(settings)
    config.set_session_factory(SignedCookieSessionFactory(settings.get('pyramid_session.secret', 'itsaseekreet')))
    config.include('pyramid_jinja2')
    config.include('tutorweb_quizdb.material.render')
    config.include('tutorweb_quizdb.material.update')
    config.include('tutorweb_quizdb.subscriptions.list')
    config.include('tutorweb_quizdb.stage')
    config.include('tutorweb_quizdb.student')

    return config.make_wsgi_app()
