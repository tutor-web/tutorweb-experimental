import unittest

from pyramid import testing

from tutorweb_quizdb.csv_renderer import CSVRenderer


class CSVRendererTest(unittest.TestCase):
    def test_call(self):
        def render(content_type=None, **kwargs):
            request = testing.DummyRequest('GET')
            if content_type:
                request.response.content_type = content_type
            return CSVRenderer({})(kwargs, dict(request=request)), request.response

        # Sets content_type
        body, response = render(results=[['hello', 'there']])
        self.assertEqual(response.content_type, 'text/csv')
        self.assertEqual(response.content_disposition, None)
        self.assertEqual(body, 'hello,there\r\n')

        # Sets filename if asked
        body, response = render(results=[['hello'], ['there']], filename='moo')
        self.assertEqual(response.content_type, 'text/csv')
        self.assertEqual(response.content_disposition, 'attachment;filename=moo.csv')
        self.assertEqual(body, 'hello\r\nthere\r\n')
