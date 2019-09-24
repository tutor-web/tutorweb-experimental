import html
import re

from html5css3 import Writer as Html5Writer
from docutils.core import publish_string
from docutils.utils import SystemMessage


def to_rst(incoming):
    """Convert RST -> HTML"""
    try:
        out = publish_string(
            source=incoming,
            writer_name='html5',
            writer=Html5Writer()
        ).decode('utf8')
    except Exception as e:
        return '<b>Error: %s</b>' % html.escape(str(e))

    m = re.search(r'<body>(.*?)</body>', out, re.DOTALL)
    return m.group(1) if m else out


def rst_render(request):
    """Convert 'data' in request body to HTML fragment"""
    incoming = request.json_body['data'] if request.body else ""

    return dict(
        html=to_rst(incoming),
    )


def includeme(config):
    config.add_view(rst_render, route_name='rst_render', renderer='json')
    config.add_route('rst_render', '/rst/render')
