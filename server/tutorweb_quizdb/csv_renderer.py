import csv
from io import StringIO


class CSVRenderer(object):
    """https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/templates/customrenderers.html"""
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        """ Returns a plain CSV-encoded string with content-type
        ``text/csv``. The content-type may be overridden by
        setting ``request.response.content_type``."""

        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'text/csv'
            if value.get('filename', None):
                response.content_disposition = 'attachment;filename=%s.csv' % value['filename']

        fout = StringIO()
        writer = csv.writer(fout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerows(value['results'])

        return fout.getvalue()


def includeme(config):
    config.add_renderer('csv', 'tutorweb_quizdb.csv_renderer.CSVRenderer')
