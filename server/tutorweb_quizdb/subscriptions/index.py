import urllib.parse

from pyramid.httpexceptions import HTTPNotFound

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
from tutorweb_quizdb.student import get_current_student


def add_syllabus(out, path, extras, level=0):
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
        n.update(extras)
        return n
    return add_syllabus(n, path, extras, level + 1)


def view_subscription_list(request):
    student = get_current_student(request)

    # Build up tree structure to syllabuss, and a flat id->dict lookup
    out_root = dict(children=[])
    out_syllabus = dict()
    for (subscribed_syllabus_id, syllabus_id, title, path, supporting_material_href) in DBSession.execute(
            """
            SELECT l.syllabus_id subscribed_syllabus_id
                 , sub_l.syllabus_id, sub_l.title, sub_l.path, sub_l.supporting_material_href
            FROM syllabus l, subscription s, syllabus sub_l
            WHERE s.syllabus_id = l.syllabus_id
            AND s.user_id = :user_id
            AND sub_l.requires_group_id = ANY(:group_ids)
            AND sub_l.path <@ l.path
            ORDER BY l.path, sub_l.path
            """, dict(
                user_id=student.user_id,
                group_ids=[g.id for g in student.groups],
            )).fetchall():
        path = Ltree(path)
        if subscribed_syllabus_id == syllabus_id:
            # We're looking at the root of a subscription, so we don't want to
            # consider anything above this point in the path
            base_level = len(path) - 1
        extras = dict(title=title)
        if supporting_material_href:
            extras['supporting_material_href'] = supporting_material_href
        out_syllabus[syllabus_id] = add_syllabus(
            out_root,
            Ltree(path),
            extras,
            level=base_level
        )

    # Using the id->dict lookup, decorate structure with all available stages
    for db_stage in (DBSession.query(Base.classes.stage)
                     .filter(Base.classes.stage.syllabus_id.in_(out_syllabus.keys()))
                     .filter_by(next_stage_id=None)
                     .order_by(Base.classes.stage.stage_name)):
        out_syllabus[db_stage.syllabus_id]['children'].append(dict(
            stage=db_stage.stage_name,
            title=db_stage.title,
            href='/api/stage?%s' % urllib.parse.urlencode(dict(
                path=str(out_syllabus[db_stage.syllabus_id]['path'] + Ltree(db_stage.stage_name)),
            )),
        ))

    return out_root


def view_subscription_add(request):
    student = get_current_student(request)
    path = Ltree(request.params['path'])

    # Find the syllabus item
    try:
        dbl = (DBSession.query(Base.classes.syllabus)
                        .filter_by(host_id=ACTIVE_HOST, path=path)
                        .filter(Base.classes.syllabus.requires_group_id.in_(g.id for g in student.groups))
                        .one())
    except NoResultFound:
        raise HTTPNotFound(path)

    # Add subscription
    try:
        DBSession.add(Base.classes.subscription(
            user=student,
            syllabus=dbl,
        ))
        DBSession.flush()
    except IntegrityError:
        # Already there
        pass

    return dict(success=True, path=path)


def includeme(config):
    config.add_view(view_subscription_list, route_name='view_subscription_list', renderer='json')
    config.add_route('view_subscription_list', '/subscriptions/list')
    config.add_view(view_subscription_add, route_name='view_subscription_add', renderer='json')
    config.add_route('view_subscription_add', '/subscriptions/add')
