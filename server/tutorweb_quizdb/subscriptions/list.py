import git
import os
import re

import rpy2
import rpy2.robjects as robjects

from pyramid.view import view_config

from tutorweb_quizdb import DBSession, Base


MATERIAL_BANK = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../db/material_bank'))  # TODO: This should be configured centrally, somewhere.

def rlist_to_dict(a):
    """
    Take R ListVector, turn it into a dict
    """
    return dict(zip(a.names, map(list,list(a))))

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


def subscription_list(student):
    out = []
    for (db_sub, db_tut) in (DBSession.query(Base.classes.subscription, Base.classes.tutorial)
            .filter_by(student=student).filter_by(hidden=False)
            .order_by(Base.classes.subscription.path)):
        out.append(dict(
            path=db_tut.path,
            title=db_tut.title,
            children=[],
        ))
        tut_grade = 0
        # TODO: We only want latest-version lectures
        for db_lec in (DBSession.query(Base.classes.lecture)
                .filter_by(tutorial=db_tut)
                .order_by(Base.classes.lecture.name)):
            out[-1]['children'].append(dict(
                name=db_lec.name,
                title=db_lec.title,
                grade=5,
                children=[],
            ))
            tut_grade += out[-1]['children'][-1]['grade']
            for db_stage in (DBSession.query(Base.classes.lecturestage)
                    .filter_by(lecture=db_lec)
                    .order_by(Base.classes.lecturestage.stage)):
                out[-1]['children'][-1]['children'].append(dict(
                    stage=db_stage.stage,
                    title=db_stage.title,
                ))
            
        out[-1]['grade'] = tut_grade / len(out[-1]['children'])

        return out


def view_subscriptions_list(request):
    # TODO: Hack in me
    student = (DBSession.query(Base.classes.student)
        .filter_by(hostdomain='ui-tutorweb3.clifford.shuttlethread.com')
        .filter_by(username='lentinj')
        .one())

    return subscription_list(student)


def includeme(config):
    config.add_view(view_subscriptions_list, route_name='view_subscriptions_list', renderer='json')
    config.add_route('view_subscriptions_list', '/subscriptions/list')
