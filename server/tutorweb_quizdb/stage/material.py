from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
from tutorweb_quizdb.material.render import material_render
from tutorweb_quizdb.student import get_current_student
from .allocation import get_allocation
from .index import update_stats, stage_get
from .setting import getStudentSettings


def stage_material(alloc, requested_ids):
    # Turn requested_material into ms / permutation tuple
    requested_material = [
        (DBSession.query(Base.classes.material_source).filter_by(material_source_id=mss_id).one(), permutation)
        for mss_id, permutation in requested_ids
    ]

    out = dict(
        stats=[
            dict(
                uri=alloc.to_public_id(ms.material_source_id, permutation),
                initial_answered=ms.initial_answered,
                initial_correct=ms.initial_correct,
                _type='regular',  # TODO: ...or historical?
            ) for ms, permutation in requested_material
        ],
        data={},
    )
    update_stats(alloc, out['stats'])

    for ms, permutation in requested_material:
        rendered = material_render(ms, permutation)
        out['data'][alloc.to_public_id(ms.material_source_id, permutation)] = rendered
    return out


def view_stage_material(request):
    """
    Get one, or all material for a stage
    """
    db_stage = stage_get(ACTIVE_HOST, request.params['path'])
    db_student = get_current_student(request)
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)

    if (request.params.get('id', None)):
        requested_material = [alloc.from_public_id(request.params['id'])]
    else:
        requested_material = alloc.get_material()
    return stage_material(alloc, requested_material)


def includeme(config):
    config.add_view(view_stage_material, route_name='stage_material', renderer='json')
    config.add_route('stage_material', '/stage/material')
