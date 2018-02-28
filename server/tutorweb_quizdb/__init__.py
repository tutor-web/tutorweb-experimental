from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = automap_base()


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
    config.include('pyramid_jinja2')

    config.add_route('view_material_update', '/material/update', request_method='POST')
    config.scan('tutorweb_quizdb.material')

    return config.make_wsgi_app()
