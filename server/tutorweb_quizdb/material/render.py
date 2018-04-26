import os

import rpy2.robjects as robjects

from tutorweb_quizdb import DBSession, Base


def rlist_to_dict(a):
    """
    Take R ListVector, turn it into a dict
    """
    return dict(zip(a.names, map(list, list(a))))


def render(path, permutation, material_bank):
    """
    Render a question
    """
    # Is this permutation even a question?
    ms = DBSession.query(Base.classes.material_source).filter_by(path=path, next_revision=None).one()
    if ms.permutation_count > permutation:
        raise ValueError("Question %s only has %d permutations, not %d" % (
            path,
            ms.permutation_count,
            permutation,
        ))

    # TODO: Caching of question objects?
    robjects.r('''question <- function () stop("R question script did not define a question function")''')
    robjects.r('''setwd''')(os.path.dirname(os.path.join(material_bank, path)))
    robjects.r('''source''')(os.path.basename(path))
    # TODO: data.frames support

    rob = robjects.globalenv['question'](permutation, [])
    # TODO: Stacktraces?

    rv = {}
    for i, name in enumerate(rob.names):
        if name == 'content':
            rv[name] = "".join(rob[i])
        elif name == 'correct':
            rv[name] = rlist_to_dict(rob[i])
        else:
            raise ValueError("Unknown return value from R question %s - %s" % (path, name))
    if 'content' not in rv:
        raise ValueError("R question %s did not return 'content'" % path)
    return rv


def view_material_render(request):
    return render(
        path=request.params['path'],
        permutation=int(request.params['permutation']),
        material_bank=request.registry.settings['tutorweb.material_bank'],
    )


def includeme(config):
    config.add_view(view_material_render, route_name='view_material_render', renderer='json')
    config.add_route('view_material_render', '/material/render')
