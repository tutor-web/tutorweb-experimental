import logging
import pprint

logger = logging.getLogger(__package__)


def view_logerror(request):
    """Dump JS errors into the log"""
    pp = pprint.PrettyPrinter(indent=2)
    messages = []

    messages.append('user: %s' % request.user)
    messages.append('user-agent: "%s"' % (request.user_agent or 'unknown'))

    logger.warn(
        'Clientside error %s:\n%s',
        ' '.join('(%s)' % m for m in messages),
        pp.pformat(request.json),
    )
    return dict(logged=True)


def includeme(config):
    config.add_view(view_logerror, route_name='logerror', renderer='json')
    config.add_route('logerror', '/logerror')
