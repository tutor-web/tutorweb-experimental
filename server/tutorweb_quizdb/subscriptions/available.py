from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, ACTIVE_HOST
from tutorweb_quizdb.student import get_current_student, student_check_group


def view_subscription_available(request):
    """Get a tree of possible things to subscribe to"""
    student = get_current_student(request)

    # Build up tree structure to syllabuss, and a flat id->dict lookup
    out = dict(children=[])
    for (syllabus_id, path, title, supporting_material_href, is_subscribed) in DBSession.execute(
            """
            SELECT l.syllabus_id, l.path, l.title, l.supporting_material_href, s.user_id IS NOT NULL AS subscribed
            FROM syllabus l
            LEFT JOIN subscription s ON s.syllabus_id = l.syllabus_id AND s.user_id = :user_id
            WHERE l.host_id = :host_id
              AND (l.requires_group_id IS NULL OR l.requires_group_id = ANY(:group_ids))
            ORDER BY l.path
            """, dict(
                host_id=ACTIVE_HOST,
                user_id=student.user_id,
                group_ids=[g.id for g in student.groups],
            )).fetchall():
        path = Ltree(path)

        # Search our tree for parents of this item
        out_pointer = out
        subscribed = path if is_subscribed else None
        for i in range(1, len(path)):
            for c in out_pointer['children']:
                if c['path'] == path[:i]:
                    out_pointer = c
                    if subscribed is None and c['subscribed']:
                        # Item in our parentage is subscribed, so we are too
                        subscribed = c['path']
                    break
            else:
                raise ValueError("Missing parent for %s" % path)

        # Found a home for this item, add it
        out_pointer['children'].append(dict(
            path=path,
            title=title,
            subscribed=subscribed,
            supporting_material_href=supporting_material_href,
            can_admin=student_check_group(student, 'admin.%s' % path),
            children=[],
        ))
    return out


def includeme(config):
    config.add_view(view_subscription_available, route_name='view_subscription_available', renderer='json')
    config.add_route('view_subscription_available', '/subscriptions/available')
