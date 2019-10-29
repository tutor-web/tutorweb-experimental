import itertools
import random

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, models, ACTIVE_HOST
from tutorweb_quizdb.student import get_group
from tutorweb_quizdb.subscriptions.index import subscription_add


def trigger_forgot_password(request, user):
    """
    Rip out forgot password logic from pluserable.views.ForgotPasswordView

    Obviously not the right thing to do, but running out of time
    """
    from pyramid.url import route_url
    from pyramid_mailer import get_mailer
    from pyramid_mailer.message import Message
    from kerno.web.pyramid import IKerno
    from pluserable.strings import get_strings

    # Assign new activation code to user
    user.activation = models.Activation()
    DBSession.flush()

    Str = get_strings(request.registry.getUtility(IKerno))

    mailer = get_mailer(request)
    username = getattr(user, 'short_name', '') or \
        getattr(user, 'full_name', '') or \
        getattr(user, 'username', '') or user.email
    body = Str.reset_password_email_body.format(
        link=route_url('reset_password', request, code=user.activation.code),
        username=username, domain=request.application_url)
    subject = Str.reset_password_email_subject
    message = Message(subject=subject, recipients=[user.email], body=body)
    mailer.send(message)


def create_student(request,
                   user_name,
                   email=None,
                   assign_password=False,
                   group_names=[],
                   subscribe=[]):
    """
    Add a new student
    - request: Pyramid request (needed to get mailer)
    - user_name: The new user-name
    - email: E-mail address, defaults to the same as the user_name
    - assign_password: If true, assign a password to any new student, otherwise mail them
    - subscribe: Tutorials to subscribe this user to, adding them to any relevant groups
    """
    if not email:
        email = user_name
    password = None

    try:
        db_u = DBSession.query(models.User).filter_by(host_id=ACTIVE_HOST, user_name=user_name).one()
        db_u.email = email
    except NoResultFound:
        password = generate_password(10)
        db_u = models.User(
            host_id=ACTIVE_HOST,
            user_name=user_name,
            email=email,
            password=password
        )
        DBSession.add(db_u)
        DBSession.flush()

        if not assign_password:
            # Send an e-mail, forget the generated password
            trigger_forgot_password(request, db_u)
            password = None
    DBSession.flush()

    # Make sure user is part of all the required groups
    for n in group_names:
        g = get_group(n, auto_create=True)
        if g not in db_u.groups:
            db_u.groups.append(g)
    DBSession.flush()

    # Make sure user is subscribed to everything required
    for s in subscribe:
        subscription_add(db_u, Ltree(s), add_to_group=True)
    DBSession.flush()

    return (db_u, password)


def generate_password(length):
    """
    Generate a password

    https://exyr.org/2011/random-pronounceable-passwords/
    """
    def pronounceable_password():
        # I omitted some letters I don’t like
        vowels = 'aiueo'
        consonants = 'bdfgjklmnprstvwxz'
        while 1:
            yield random.choice(consonants)
            yield random.choice(vowels)
    return ''.join(itertools.islice(pronounceable_password(), length))


def includeme(config):
    pass


def script_student_import():
    import argparse
    import sys
    from tutorweb_quizdb import setup_script

    argparse_arguments = [
        dict(description='Create many users in one go'),
        dict(
            name='infile',
            type=argparse.FileType('r'),
            default=sys.stdin),
        dict(
            name='--groups',
            help='Groups to make sure these users are in (comma-separated)',
            nargs='?',
            default=''),
        dict(
            name='--email-address',
            help='Email address to use for users, if not given use user_name',
            nargs='?',
            default=None),
        dict(
            name='--assign-passwords',
            help='Generate passwords for each user, print in output',
            action="store_true"),
        dict(
            name='--subscribe',
            help='Subscribe student to tutorial',
            action='append',
            default=[]),
    ]

    with setup_script(argparse_arguments) as env:
        with env['args'].infile as f:
            new_user_names = filter(None, f.readlines())

        for new_user_name in new_user_names:
            new_user_name = new_user_name.strip()
            if not new_user_name:
                continue

            # Create user and print output
            (new_user, password) = create_student(
                env['request'],
                new_user_name,
                env['args'].email_address or new_user_name,
                assign_password=env['args'].assign_passwords,
                group_names=env['args'].groups.split(','),
                subscribe=env['args'].subscribe,
            )
            print("%s,%s,%s" % (
                new_user.user_name,
                new_user.email,
                password or '',
            ))
