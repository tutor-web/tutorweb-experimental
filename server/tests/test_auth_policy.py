import unittest

from http import cookies
from pyramid.security import remember

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.auth.policy import includeme as auth_includeme, read_machine_id, get_user


class ReadMachineIdTest(unittest.TestCase):
    def test_call(self):
        """Read the machine ID file of the current computer"""
        self.assertTrue(len(read_machine_id()) > 30)


class GetUserTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    def test_call(self):
        """get_user turns request into user"""
        auth_includeme(self.config)
        self.db_studs = self.create_students(1)

        req = self.request()
        self.assertEqual(get_user(req), None)

        # Remember who we are, now get user back
        C = cookies.SimpleCookie()
        C.load(remember(req, self.db_studs[0].id)[0][1])
        req.cookies = {k: v.value for k, v in C.items()}
        self.assertEqual(get_user(req), self.db_studs[0])
