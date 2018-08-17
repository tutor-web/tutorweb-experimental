import itertools
import random

from sqlalchemy.orm.exc import NoResultFound

from tutorweb_quizdb import DBSession, models, ACTIVE_HOST


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
                   groups=[]):
    """
    Add a new student
    - request: Pyramid request (needed to get mailer)
    - user_name: The new user-name
    - email: E-mail address, defaults to the same as the user_name
    - assign_password: If true, assign a password to any new student, otherwise mail them
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
    for g in groups:
        if g not in db_u.groups:
            db_u.groups.append(g)

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
