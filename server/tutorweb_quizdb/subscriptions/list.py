import os
import urllib.parse

import rpy2.robjects as robjects

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.student import get_current_student


MATERIAL_BANK = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../db/material_bank'))  # TODO: This should be configured centrally, somewhere.


def rlist_to_dict(a):
    """
    Take R ListVector, turn it into a dict
    """
    return dict(zip(a.names, map(list, list(a))))


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
    robjects.r('''setwd''')(os.path.dirname(os.path.join(MATERIAL_BANK, path)))
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


def view_subscription_list(request):
    student = get_current_student(request)

    out = []
    for (db_sub, db_tut) in (DBSession.query(Base.classes.subscription, Base.classes.tutorial)
                             .filter_by(user=student).filter_by(hidden=False)
                             .order_by(Base.classes.subscription.path)):
        out.append(dict(
            path=db_tut.path,
            title=db_tut.title,
            children=[],
        ))
        tut_grade = 0
        for db_lec in (DBSession.query(Base.classes.lecture)
                       .filter_by(tutorial=db_tut)
                       .order_by(Base.classes.lecture.lecture_name)):
            out[-1]['children'].append(dict(
                name=db_lec.lecture_name,
                title=db_lec.title,
                grade=5,
                children=[],
            ))
            tut_grade += out[-1]['children'][-1]['grade']
            for db_stage in (DBSession.query(Base.classes.stage)
                             .filter_by(lecture=db_lec)
                             .filter_by(next_version=None)
                             .order_by(Base.classes.stage.stage_name)):
                out[-1]['children'][-1]['children'].append(dict(
                    stage=db_stage.stage_name,
                    title=db_stage.title,
                    grade=2,
                    href='/api/stage?%s' % urllib.parse.urlencode(dict(
                        path=os.path.normpath(os.path.join(db_tut.path, db_lec.lecture_name, db_stage.stage_name)),
                    )),
                ))
        out[-1]['grade'] = tut_grade / len(out[-1]['children'])

        return dict(children=out)


def includeme(config):
    config.add_view(view_subscription_list, route_name='view_subscription_list', renderer='json')
    config.add_route('view_subscription_list', '/subscriptions/list')
