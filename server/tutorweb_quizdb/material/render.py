import os

import rpy2.robjects as robjects

from tutorweb_quizdb import DBSession, Base
from .usergenerated import ug_render


def rob_to_dict(a):
    """
    Take R Object and turn it into something JSON-parsable
    """
    if isinstance(a, robjects.vectors.ListVector):
        return dict(zip(a.names, [rob_to_dict(x) for x in a]))
    else:
        return list(a)


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


def r_render(ms, permutation):
    """Execute R script to generate content"""
    # TODO: Caching of question objects?
    robjects.r('''question <- function () stop("R question script did not define a question function")''')
    robjects.r('''setwd''')(os.path.dirname(os.path.join(ms.bank, ms.path)))
    robjects.r('''source''')(os.path.basename(ms.path))
    # TODO: data.frames support

    rob = robjects.globalenv['question'](permutation, [])
    # TODO: Stacktraces?
    try:
        rv = rob_to_dict(rob)
    except Exception as e:
        raise ValueError("R question output not parsable %s\n%s" % (rob, e))

    if 'content' not in rv:
        raise ValueError("R question %s did not return 'content'" % ms.path)
    rv['content'] = "".join(rv['content'])
    return rv


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
