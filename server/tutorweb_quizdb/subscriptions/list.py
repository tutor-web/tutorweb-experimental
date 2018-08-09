import urllib.parse

from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.student import get_current_student


def add_lec(out, path, title, level=0):
    path_head = str(path[level])

    # Search for path in children
    for n in out['children']:
        if n['name'] == path_head:
            break
    else:
        # Couldn't find it, add it
        out['children'].append(dict(
            name=path_head,
            path=path[:level + 1],
            children=[],
        ))
        n = out['children'][-1]

    if level + 1 >= len(path):
        n['title'] = title
        return n
    return add_lec(n, path, title, level + 1)


def view_subscription_list(request):
    student = get_current_student(request)

    # Build up tree structure to lectures, and a flat id->dict lookup
    out_root = dict(children=[])
    out_lec = dict()
    for (subscribed_lecture_id, lecture_id, title, path) in DBSession.execute(
            """
            SELECT l.lecture_id subscribed_lecture_id
                 , sub_l.lecture_id, sub_l.title, sub_l.path
            FROM lecture l, subscription s, lecture sub_l
            WHERE s.lecture_id = l.lecture_id
            AND s.hidden = FALSE
            AND s.user_id = :user_id
            AND sub_l.path <@ l.path
            ORDER BY l.path, sub_l.path
            """, dict(
                user_id=student.user_id,
            )).fetchall():
        path = Ltree(path)
        if subscribed_lecture_id == lecture_id:
            # We're looking at the root of a subscription, so we don't want to
            # consider anything above this point in the path
            base_level = len(path) - 1
        out_lec[lecture_id] = add_lec(out_root, Ltree(path), title, level=base_level)

    # Using the id->dict lookup, decorate structure with all available stages
    for db_stage in (DBSession.query(Base.classes.stage)
                     .filter(Base.classes.stage.lecture_id.in_(out_lec.keys()))
                     .filter_by(next_version=None)
                     .order_by(Base.classes.stage.stage_name)):
        out_lec[db_stage.lecture_id]['children'].append(dict(
            stage=db_stage.stage_name,
            title=db_stage.title,
            href='/api/stage?%s' % urllib.parse.urlencode(dict(
                path=str(out_lec[db_stage.lecture_id]['path'] + Ltree(db_stage.stage_name)),
            )),
        ))

    return out_root


def includeme(config):
    config.add_view(view_subscription_list, route_name='view_subscription_list', renderer='json')
    config.add_route('view_subscription_list', '/subscriptions/list')
