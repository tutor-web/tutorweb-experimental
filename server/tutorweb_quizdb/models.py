import datetime

import cryptacular.bcrypt
from bag.text.hash import random_hash
import sqlalchemy as sa
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.ext.declarative import declared_attr

from tutorweb_quizdb import Base


crypt = cryptacular.bcrypt.BCRYPTPasswordManager()


class UserBase:
    """Base class for a User model."""

    def __init__(self, email, password, salt=None, activation=None, **kw):
        """User constructor."""
        # print('User constructor: {} / {} / {} / {}'.format(
        #     email, password, salt, activation))
        self.email = email
        assert self.email and isinstance(self.email, str)
        self.salt = salt or random_hash(24)
        self.password = password
        assert self.password and isinstance(self.password, str)
        self.activation = activation
        for k, v in kw.items():
            setattr(self, k, v)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.email)

    @property
    def password(self):
        """Set the password, or retrieve the password hash."""
        return self._password

    @password.setter
    def password(self, value):
        self._password = self._hash_password(value)

    def _hash_password(self, password):
        assert self.salt, "UserBase constructor was not called; " \
            "you probably have your User base classes in the wrong order."
        return str(crypt.encode(password + self.salt))

    def check_password(self, password):
        """Check the ``password`` and return a boolean."""
        if not password:
            return False
        return crypt.check(self.password, password + self.salt)

    @property
    def is_activated(self):
        """False if this user needs to confirm her email address."""
        return self.activation is None

    # @property
    # def __acl__(self):
    #     return [
    #         (Allow, 'user:%s' % self.id, 'access_user')
    #     ]


class User(UserBase, Base):
    __tablename__ = 'user'
    __table_args__ = dict(
        extend_existing=True,
    )

    user_id = sa.Column(
        'user_id',
        sa.Integer,
        autoincrement=True,
        primary_key=True)
    id = synonym('user_id')

    host_id = sa.Column(
        'host_id',
        sa.Integer,
        sa.ForeignKey('host.host_id'),
        autoincrement=True,
        default=1)

    user_name = sa.Column("user_name", sa.UnicodeText)
    username = synonym('user_name')
    _password = sa.Column('pw_hash', sa.Unicode(256), nullable=False)

    groups = relationship("Group", secondary='user_group')

    # Ignore any csrf_token passed through
    @property
    def csrf_token(self):
        pass

    @csrf_token.setter
    def csrf_token(self, value):
        pass

    def add_group(self, new_group):
        """Add group only if it's not already there"""
        if new_group not in self.groups:
            self.groups.append(new_group)


class Group(Base):
    __tablename__ = 'group'
    __table_args__ = dict(
        extend_existing=True,
    )

    @declared_attr
    def id(cls):
        """Autogenerated ID"""
        return sa.Column(
            'group_id',
            sa.Integer,
            autoincrement=True,
            primary_key=True)


class UserGroup(Base):
    __tablename__ = 'user_group'

    @declared_attr
    def id(cls):
        """Autogenerated ID"""
        return sa.Column(
            'user_group_id',
            sa.Integer,
            autoincrement=True,
            primary_key=True)

    user_id = sa.Column(
        'user_id',
        sa.Integer,
        sa.ForeignKey('user.user_id')
    )

    group_id = sa.Column(
        'group_id',
        sa.Integer,
        sa.ForeignKey('group.group_id')
    )

    __table_args__ = (
        dict(
            extend_existing=True,
        ),
    )


def activation_lifetime():
    return datetime.datetime.utcnow() + datetime.timedelta(days=3)


class ActivationBase:
    """Handles activations and password reset items for users.

    ``code`` is a random hash that is valid only once.
    Once the hash is used to access the site, it is removed.

    ``valid_until`` is a datetime until when the activation key will last.

    ``created_by`` is a system: new user registration, password reset,
    forgot password etc.
    """

    def __init__(self, code=None, valid_until=None, created_by='web'):
        """Usually call with the ``created_by`` system, or no arguments."""
        self.code = code or random_hash()
        self.valid_until = valid_until or activation_lifetime()
        assert isinstance(self.valid_until, datetime.datetime)
        self.created_by = created_by


class ActivationMixin(ActivationBase):
    """Handles email confirmation codes and password reset codes for users.

    The code should be a random hash that is valid only once.
    After the hash is used to access the site, it'll be removed.

    The "created by" value refers to a system:
    new user registration, password reset, forgot password etc.
    """

    @declared_attr
    def code(self):
        """A random hash that is valid only once."""
        return sa.Column(sa.Unicode(30), nullable=False,
                         unique=True,
                         default=random_hash)

    @declared_attr
    def valid_until(self):
        """How long will the activation key last."""
        return sa.Column(sa.DateTime, nullable=False,
                         default=activation_lifetime())

    @declared_attr
    def created_by(self):
        """The system that generated the activation key."""
        return sa.Column(sa.Unicode(30), nullable=False,
                         default='web')


class Activation(ActivationMixin, Base):
    __tablename__ = 'activation'
    __table_args__ = dict(
        extend_existing=True,
    )

    @declared_attr
    def id(cls):
        """Autogenerated ID"""
        return sa.Column(
            'activation_id',
            sa.Integer,
            autoincrement=True,
            primary_key=True)
