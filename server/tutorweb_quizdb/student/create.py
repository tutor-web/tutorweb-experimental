import itertools
import random

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, models, ACTIVE_HOST
from tutorweb_quizdb.student import get_group
from tutorweb_quizdb.subscriptions.index import subscription_add


EMAIL_TEMPLATE = ["Reset your password", """\
Hello, {username}!

Someone requested resetting your password. If it was you, click here:
{link}

If you don't want to change your password, please ignore this email message.

Regards,
{domain}\n"""]


def activate_trigger_email(request, user):
    """
    Start user-activation process with an e-mail
    - (user) can either be a user object, or a string containing a user's e-mail address
    """
    from pyramid.url import route_url
    from pyramid_mailer import get_mailer
    from pyramid_mailer.message import Message

    # Find user object if need be
    if isinstance(user, str):
        handle = user
        user = DBSession.query(models.User).filter_by(
            host_id=ACTIVE_HOST,
            email=handle,
        ).first()
        if not user:
            user = DBSession.query(models.User).filter_by(
                host_id=ACTIVE_HOST,
                username=handle,
            ).first()

    if not user:
        return

    # Assign new activation code to user
    user.activation = models.Activation()
    DBSession.flush()

    mailer = get_mailer(request)
    username = getattr(user, 'short_name', '') or \
        getattr(user, 'full_name', '') or \
        getattr(user, 'username', '') or user.email
    subject = EMAIL_TEMPLATE[0]
    body = EMAIL_TEMPLATE[1].format(
        link=route_url('auth_activate_finalize', request, code=user.activation.code),
        username=username, domain=request.application_url)
    message = Message(subject=subject, recipients=[user.email], body=body)
    mailer.send(message)


def activate_set_password(request, activation, new_pwd):
    """Given an activation code, set a user's password"""
    # Find activation object if need be
    if isinstance(activation, str):
        activation = DBSession.query(models.Activation).filter_by(code=activation).first()
    if not activation:
        raise ValueError("Activation code has expired, or never existed")

    user = DBSession.query(models.User).filter_by(
        host_id=ACTIVE_HOST,
        activation_id=activation.id,
    ).one()
    user.password = new_pwd
    user.activation = None
    DBSession.delete(activation)
    DBSession.flush()


def create_student(request,
                   user_name,
                   email=None,
                   assign_password=False,
                   must_not_exist=False,
                   group_names=[],
                   subscribe=[]):
    """
    Add a new student
    - request: Pyramid request (needed to get mailer)
    - user_name: The new user-name
    - email: E-mail address, defaults to the same as the user_name
    - assign_password: If true, assign a password to any new student, otherwise mail them
    - must_not_exist: If true, raise an error if student already exists
    - subscribe: Tutorials to subscribe this user to, adding them to any relevant groups
    """
    if not email:
        email = user_name
    password = None

    try:
        db_u = DBSession.query(models.User).filter_by(host_id=ACTIVE_HOST, user_name=user_name).one()
        db_u.email = email
        if must_not_exist:
            raise ValueError('The username %s is already taken' % user_name)
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
            activate_trigger_email(request, db_u)
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
    from tutorweb_quizdb import setup_script

    argparse_arguments = [
        dict(description='Create many users in one go'),
        dict(
            name='infile',
            help='File of newline-separated usernames to read',
            type=argparse.FileType('r'),
            nargs='?',
            default=None),
        dict(
            name='--user',
            help='User(s) to add/modify (if not provided by infile)',
            action='append',
            default=[]),
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
        new_user_names = env['args'].user
        if env['args'].infile:
            with env['args'].infile as f:
                new_user_names += filter(None, f.readlines())
        if len(new_user_names) == 0:
            print("No users to add/modify")
            env['argparser'].print_help()
            exit(1)

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
