import logging

from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest
)

logger = logging.getLogger(__package__)


def view_exception(e, request):
    import traceback

    level = getattr(e, 'level', 'error')
    print_stack = getattr(e, 'print_stack', True)
    request.response.status = getattr(e, 'status_code', 500)
    if getattr(e, 'status_code', 500) == 500:
        logging.exception(e)

    return {level: dict(
        type=e.__class__.__name__,
        message=(e.__class__.__name__ + ": " if print_stack else "") + str(e),
        stack=traceback.format_exc() if print_stack else None,
    )}


def includeme(config):
    for e_class in (Exception, HTTPForbidden, HTTPBadRequest):
        config.add_exception_view(view_exception, e_class, accept='text/html', renderer='templates/exceptions.mako')
        config.add_exception_view(view_exception, e_class, accept='application/json', renderer='json')
