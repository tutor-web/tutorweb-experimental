import unittest

from pyramid import testing

from tutorweb_quizdb.logerror import view_logerror


class ViewLogErrorTest(unittest.TestCase):
    def test_call(self):
        def logerror(obj_in, user="ut_user", user_agent=None):
            request = testing.DummyRequest('GET')
            request.user = user
            request.user_agent = user_agent
            request.json = obj_in

            with self.assertLogs('', level="WARN") as cm:
                out = view_logerror(request)
                self.assertEqual(out, dict(logged=True))
            return cm.output

        self.assertEqual(logerror(dict(a=1, b=2)), [
            'WARNING:tutorweb_quizdb:Clientside error (user: ut_user) (user-agent: "unknown"):\n{\'a\': 1, \'b\': 2}'
        ])

        self.assertEqual(logerror(dict(a=1, c=9), user='frank', user_agent='mosaic'), [
            'WARNING:tutorweb_quizdb:Clientside error (user: frank) (user-agent: "mosaic"):\n{\'a\': 1, \'c\': 9}'
        ])
