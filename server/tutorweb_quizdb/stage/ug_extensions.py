from .index import alloc_for_view
from .answer_queue import request_review


def view_stage_request_review(request):
    """
    Request to review some material for this allocation, assuming alloc has
    template questions

    params:
    - path: Stage path
    """
    alloc = alloc_for_view(request)
    return request_review(alloc)


def includeme(config):
    config.add_view(view_stage_request_review, route_name='stage_request_review', renderer='json')
    config.add_route('stage_request_review', '/stage/request-review')
