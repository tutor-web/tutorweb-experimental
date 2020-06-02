import unittest
import re

from pyramid_mailer import get_mailer

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid


class AuthFunctionalTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    def test_auth(self):
        """Test logging in/out. registering"""
        testapp = self.functional_test()
        mailer = get_mailer(testapp.app.registry)

        # Get login form on first try
        res = testapp.get('/auth/login', status=200)
        self.assertEqual(
            set(res.form.fields.keys()),
            set(('password', 'csrf_token', 'handle', '__formid__', 'submit', '_charset_')))

        # Submit invalid user, bounced back to form
        res.form.set('handle', 'parrot@example.com')
        res.form.set('password', 'parrotpwd')
        res = res.form.submit()
        self.assertIn('Invalid username / password', res.body.decode('utf8'))
        self.assertEqual(
            set(res.form.fields.keys()),
            set(('password', 'csrf_token', 'handle', '__formid__', 'submit', '_charset_')))

        # Register ourselves
        res = testapp.get('/auth/register', status=200)
        self.assertEqual(
            set(res.form.fields.keys()),
            set(('csrf_token', 'handle', 'email', '__formid__', 'submit', '_charset_')))
        res.form.set('handle', 'parrot@example.com')
        res.form.set('email', 'parrot@example.com')
        res = res.form.submit()
        self.assertIn('check your e-mail inbox', res.body.decode('utf8'))
        self.assertEqual(res.forms, {})

        # Without answering e-mail, still get the same response
        res = testapp.get('/auth/login', status=200)
        res.form.set('handle', 'parrot@example.com')
        res.form.set('password', 'parrotpwd')
        res = res.form.submit()
        self.assertIn('Invalid username / password', res.body.decode('utf8'))

        # We got a message
        self.assertEqual(len(mailer.outbox), 1)
        self.assertIn('parrot@example.com', mailer.outbox[0].body)
        reset_link = re.search(r'/auth/reset-password/[\w]+', mailer.outbox[0].body).group(0)

        # Follow the link, get logged in
        res = testapp.get(reset_link, status=200)
        self.assertEqual(
            set(res.form.fields.keys()),
            set(('password', 'password-confirm', 'csrf_token', 'submit', '_charset_', '__start__', '__end__', '__formid__')))
        res.form.set('password', 'parrotpwd')
        res.form.set('password-confirm', 'parrotpwd')
        res = res.form.submit()
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/')

        # Can log in ourselves
        res = testapp.get('/auth/login', status=200)
        res.form.set('handle', 'parrot@example.com')
        res.form.set('password', 'parrotpwd')
        res = res.form.submit()
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://localhost/')

        # Now login form just logs us straight in
        res = testapp.get('/auth/login', status=302)
        self.assertEqual(res.location, 'http://localhost/')

        # Logout, and we just get the form again
        res = testapp.get('/auth/logout', status=302)
        self.assertEqual(res.location, 'http://localhost/')
        res = testapp.get('/auth/login', status=200)
        self.assertEqual(
            set(res.form.fields.keys()),
            set(('password', 'csrf_token', 'handle', '__formid__', 'submit', '_charset_')))
