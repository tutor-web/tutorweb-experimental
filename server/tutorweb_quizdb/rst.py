import html
import io
import re

from html5css3 import Writer as Html5Writer
from docutils.core import publish_string


MESSAGE_TEMPLATE = '<div class="system-message %s"><div class="system-message-title">System message:</div>%s</div>'


def to_rst(incoming):
    """Convert RST -> HTML"""
    warnings = io.StringIO()
    try:
        out = publish_string(
            source=incoming,
            writer_name='html5',
            writer=Html5Writer(),
            settings_overrides=dict(
                warning_stream=warnings,
            ),
        ).decode('utf8')
    except Exception as e:
        return (MESSAGE_TEMPLATE % ('severe', html.escape(str(e)))) + ('<pre>%s</pre>' % html.escape(incoming))

    m = re.search(r'<body>(.*?)</body>', out, re.DOTALL)
    if m:
        out = m.group(1)

    # Convert warnings into a list of lines
    warnings.seek(0)
    out = "".join(MESSAGE_TEMPLATE % ('warning', html.escape(l)) for l in warnings.readlines()) + out

    return out


def rst_render(request):
    """Convert 'data' in request body to HTML fragment"""
    incoming = request.json_body['data'] if request.body else ""

    return dict(
        html=to_rst(incoming),
    )


def includeme(config):
    config.add_view(rst_render, route_name='rst_render', renderer='json')
    config.add_route('rst_render', '/rst/render')
