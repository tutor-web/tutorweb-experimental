import os
import urllib.parse

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.student import get_current_student


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
