import os

import rpy2.robjects as robjects

from tutorweb_quizdb import DBSession, Base


def rlist_to_dict(a):
    """
    Take R ListVector, turn it into a dict
    """
    return dict(zip(a.names, map(list, list(a))))


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

    rv = {}
    for i, name in enumerate(rob.names):
        if name == 'content':
            rv[name] = "".join(rob[i])
        elif name == 'correct':
            try:
                rv[name] = rlist_to_dict(rob[i])
            except:
                raise ValueError("Correct object not parsable %s" % rob[i])
        else:
            raise ValueError("Unknown return value from R question %s - %s" % (ms.path, name))
    if 'content' not in rv:
        raise ValueError("R question %s did not return 'content'" % ms.path)
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
