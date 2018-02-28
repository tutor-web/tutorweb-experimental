import git
import os
import re

import rpy2
import rpy2.robjects as robjects

from pyramid.view import view_config

from tutorweb_quizdb import DBSession, Base


MATERIAL_BANK = '../db/material_bank'  # TODO: This should be configured centrally, somewhere.

def render(path, permutation):
    """
    Render a question
    """
    # Is this permutation even a question?
    ms = DBSession.query(Base.classes.materialsource).filter_by(path=path, nextrevision=None).one()
    if ms.permutationcount > permutation:
        raise ValueError("Question %s only has %d permutations, not %d" % (
            path,
            ms.permutationcount,
            permutation,
        ))

    # TODO: Caching of question objects?
    robjects.r('''question <- function () stop("R question script did not define a question function")''')
    with open(os.path.join(MATERIAL_BANK, path), 'r') as f:
        robjects.r(f.read())
    # TODO: data.frames support
    # TODO: Guarantees about cwd?
    rob = robjects.globalenv['question'](permutation, [])

    rv = {}
    for i, name in enumerate(rob.names):
        if name == 'content':
            rv[name] = "".join(rob[i])
        elif name == 'correct':
            rv[name] = tuple(rob[i])
        else:
            raise ValueError("Unknown return value from R question %s - %s" % (path, name))
    if 'content' not in rv:
        raise ValueError("R question %s did not return 'content'" % path)
    return rv


def view_material_render(request):
    return render(path=request.params['path'], permutation=int(request.params['permutation']))


def includeme(config):
    config.add_view(view_material_render, route_name='view_material_render', renderer='json')
    config.add_route('view_material_render', '/material/render')
