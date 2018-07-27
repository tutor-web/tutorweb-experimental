from setuptools import setup, find_packages

requires = [
    'gitpython',
    'numpy',
    'plaster_pastedeploy',
    'pluserable',
    'psycopg2',
    'pyramid',
    'pyramid_jinja2',
    'pyramid_mailer',
    'pyramid_mako',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'SQLAlchemy',
    'rpy2',
    'rst2html5-tools',
    'transaction',
    'waitress',
    'zope.sqlalchemy',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',
    'pytest-cov',
    'testing.postgresql',
]

setup(
    name='tutorweb_quizdb',
    version='0.0',
    description='Tutorweb QuizDB',
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = tutorweb_quizdb:main',
        ],
    },
)
