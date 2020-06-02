import unittest

from pyramid.httpexceptions import HTTPForbidden

from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.exceptions import view_exception


class ViewException(RequiresPyramid, unittest.TestCase):
    def test_call(self):
        out = view_exception(ValueError("moo"), self.request())
        self.assertEqual(out, dict(error=dict(
            message='ValueError: moo',
            stack='NoneType: None\n',
            type='ValueError',
        )))

        out = view_exception(HTTPForbidden(), self.request())
        self.assertEqual(out, dict(error=dict(
            message='HTTPForbidden: Access was denied to this resource.',
            stack='NoneType: None\n',
            type='HTTPForbidden',
        )))

        e = ValueError("oink")
        e.print_stack = False
        out = view_exception(e, self.request())
        self.assertEqual(out, dict(error=dict(
            message='oink',
            stack=None,
            type='ValueError',
        )))
