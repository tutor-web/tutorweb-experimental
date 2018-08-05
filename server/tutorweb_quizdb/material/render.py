from tutorweb_quizdb import DBSession, Base
from .renderer.usergenerated import ug_render
from .renderer.r import r_render


def material_render(ms, permutation):
    """
    Render a question
    """
    if 'type.template' in ms.material_tags and permutation > ms.permutation_count:
        # For templates, permutations > ms.permutation_count are user-generated material
        out = ug_render(ms, permutation)
    elif ms.permutation_count < permutation:
        # Otherwise, permutation should be in range
        raise ValueError("Question %s only has %d permutations, not %d" % (
            ms.path,
            ms.permutation_count,
            permutation,
        ))
    elif ms.path.endswith('.R'):
        out = r_render(ms, permutation)
    else:
        raise ValueError("Don't know how to render %s" % ms.path)

    # Add common extra detail to material object
    if 'tags' not in out:
        # TODO: Something more sensible to do?
        out['tags'] = ms.material_tags

    return out


def view_material_render(request):
    ms = DBSession.query(Base.classes.material_source).filter_by(
        material_bank=request.params.get('material_bank', request.registry.settings['tutorweb.material_bank.default']),
        path=request.params['path'],
        next_revision=None
    ).one()

    return material_render(
        ms,
        permutation=int(request.params['permutation']),
    )


def includeme(config):
    config.add_view(view_material_render, route_name='view_material_render', renderer='json')
    config.add_route('view_material_render', '/material/render')
