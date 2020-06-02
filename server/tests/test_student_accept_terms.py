import unittest

from pyramid.httpexceptions import HTTPForbidden

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.student import get_group
from tutorweb_quizdb.student.accept_terms import view_student_accept_terms


class ViewStudentAcceptTermsTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    def test_call(self):
        db_studs = self.create_students(1, student_group_fn=lambda i: [])

        # Need to be logged in for this to work
        with self.assertRaises(HTTPForbidden):
            view_student_accept_terms(self.request())

        # Get added to accept_terms
        self.assertEqual(
            set(u.username for u in get_group('accept_terms').users),
            set(()))
        self.assertEqual(
            view_student_accept_terms(self.request(user=db_studs[0])),
            dict(success=True))
        self.assertEqual(
            set(u.username for u in get_group('accept_terms').users),
            set((db_studs[0].username,)))

        # But only once
        self.assertEqual(
            view_student_accept_terms(self.request(user=db_studs[0])),
            dict(success=True))
        self.assertEqual(
            set(u.username for u in get_group('accept_terms').users),
            set((db_studs[0].username,)))
