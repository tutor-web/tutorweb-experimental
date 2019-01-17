from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest
)


def view_exception(e, request):
    import traceback

    level = getattr(e, 'level', 'error')
    print_stack = getattr(e, 'print_stack', True)
    request.response.status = getattr(e, 'status_code', 500)
    return {level: dict(
        type=e.__class__.__name__,
        message=(e.__class__.__name__ + ": " if print_stack else "") + str(e),
        stack=traceback.format_exc() if print_stack else None,
    )}


def includeme(config):
    config.add_exception_view(view_exception, Exception, renderer='json')
    config.add_exception_view(view_exception, HTTPForbidden, renderer='json')
    config.add_exception_view(view_exception, HTTPBadRequest, renderer='json')
