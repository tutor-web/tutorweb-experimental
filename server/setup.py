from setuptools import setup, find_packages

requires = [
    'gitpython',
    'numpy',
    'plaster_pastedeploy',
    'pluserable==0.5.0',
    'psycopg2',
    'pyramid',
    'pyramid_jinja2',
    'pyramid_mailer',
    'pyramid_mako',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'SQLAlchemy',
    'sqlalchemy-utils',
    'rpy2<3.0.0',
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
        'console_scripts': [
            'syllabus_import=tutorweb_quizdb.syllabus.add:script',
            'student_import=tutorweb_quizdb.student.create:script_student_import',
            'material_update=tutorweb_quizdb.material.update:script_material_update',
            'material_render=tutorweb_quizdb.material.render:script_material_render',
        ],
    },
)
