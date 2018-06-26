import os

import rpy2.robjects as robjects

from tutorweb_quizdb import DBSession, Base


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
    # Is this permutation even a question?
    if ms.permutation_count < permutation:
        raise ValueError("Question %s only has %d permutations, not %d" % (
            ms.path,
            ms.permutation_count,
            permutation,
        ))

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
