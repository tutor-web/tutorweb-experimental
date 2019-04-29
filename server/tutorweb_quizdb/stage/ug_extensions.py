from zope.sqlalchemy import mark_changed

from tutorweb_quizdb import DBSession
from tutorweb_quizdb.timestamp import timestamp_to_datetime

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


def view_stage_ug_rewrite(request):
    """
    Request to rewrite given question, marks as superseded and points at template

    params:
    - path: Stage path
    - uri: Old URI of question
    - time_end: Time question was answered
    """
    alloc = alloc_for_view(request)
    old_uri = request.params['uri']

    # Update any matching alllocation as rewritten, fetching old answer in process
    (old_mss_id, old_permutation) = alloc.from_public_id(old_uri)
    session = DBSession()  # Get a real session, not just a sessionmaker factory, so we can mark_changed
    r = session.execute("""
        UPDATE answer
           SET review = '{"superseded": true}'::JSONB
         WHERE user_id = :user_id
           AND material_source_id = :old_mss_id
           AND permutation = :old_permutation
           AND time_end = :time_end
     RETURNING answer_id, student_answer
    """, dict(
        user_id=alloc.db_student.id,
        # NB: We can't filter by stage_id since it might be an old stage
        old_mss_id=old_mss_id,
        old_permutation=old_permutation,
        time_end=timestamp_to_datetime(float(request.params['time_end'])),
    )).fetchall()
    if len(r) != 1:
        raise ValueError("Expected to find one answer, not %d" % len(r))
    (answer_id, student_answer) = r[0]
    mark_changed(session)  # Mark this session changed, so sqlalchemy commits

    return dict(
        uri=alloc.to_public_id(old_mss_id, old_permutation),
        student_answer=student_answer,
    )


def includeme(config):
    config.add_view(view_stage_request_review, route_name='stage_request_review', renderer='json')
    config.add_route('stage_request_review', '/stage/request-review')
    config.add_view(view_stage_ug_rewrite, route_name='stage_ug_rewrite', renderer='json')
    config.add_route('stage_ug_rewrite', '/stage/ug-rewrite')
