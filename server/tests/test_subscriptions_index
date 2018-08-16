import unittest

from sqlalchemy_utils import Ltree

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.subscriptions.list import view_subscription_list


class SubscriptionsListTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def setUp(self):
        super(SubscriptionsListTest, self).setUp()

        from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
        from tutorweb_quizdb import models
        from tutorweb_quizdb.student import student_accept_terms
        self.DBSession = DBSession

        lecture_paths = [
            'dept0',
            'dept0.tut0',
            'dept0.tut0.lec0',
            'dept0.tut0.lec1',
            'dept0.tut1',
            'dept0.tut1.lec0',
            'dept0.tut1.lec1',
            'dept1.tut2',
            'dept1.tut2.lec0',
            'dept1.tut2.lec1',
        ]

        # Add lectures
        self.db_lecs = {}
        for l in lecture_paths:
            self.db_lecs[l] = Base.classes.syllabus(host_id=ACTIVE_HOST, path=Ltree(l), title="UT Lecture %s" % l)
            DBSession.add(self.db_lecs[l])
        self.db_lecs['dept0.tut0.lec0'].supporting_material_href = 'http://wikipedia.org/'
        DBSession.flush()

        # Hang some stages off lectures
        self.db_stages = {}
        for l in lecture_paths:
            if '.lec' not in l:
                continue
            self.db_stages[l] = Base.classes.stage(
                syllabus=self.db_lecs[l],
                stage_name='stage0',
                version=0,
                title='UT stage %s.stage0' % l,
                stage_setting_spec=dict(
                    allocation_method=dict(value='passthrough'),
                ),
            )
            DBSession.add(self.db_stages[l])
        DBSession.flush()

        # Add some students
        self.db_studs = [models.User(
            host_id=ACTIVE_HOST,
            user_name='user%d' % i,
            email='user%d@example.com' % i,
            password='parp',
        ) for i in [0, 1, 2]]
        DBSession.add(self.db_studs[0])
        DBSession.add(self.db_studs[1])
        DBSession.add(self.db_studs[2])
        DBSession.flush()

        student_accept_terms(self.request(user=self.db_studs[0]))
        student_accept_terms(self.request(user=self.db_studs[1]))

    def test_call(self):
        from tutorweb_quizdb import DBSession, Base

        # make some subscriptions
        self.db_studs[0].subscription_collection.extend([
            Base.classes.subscription(syllabus=self.db_lecs['dept0.tut0']),
            Base.classes.subscription(syllabus=self.db_lecs['dept0.tut1.lec1']),
        ])
        self.db_studs[1].subscription_collection.extend([
            Base.classes.subscription(syllabus=self.db_lecs['dept0.tut1']),
        ])
        DBSession.flush()

        out = view_subscription_list(self.request(user=self.db_studs[0]))
        self.assertEqual(out, {'children': [
            {
                'name': 'tut0',
                'path': Ltree('dept0.tut0'),
                'title': 'UT Lecture dept0.tut0',
                'children': [
                    {
                        'name': 'lec0',
                        'path': Ltree('dept0.tut0.lec0'),
                        'title': 'UT Lecture dept0.tut0.lec0',
                        'supporting_material_href': 'http://wikipedia.org/',
                        'children': [
                            {
                                'href': '/api/stage?path=dept0.tut0.lec0.stage0',
                                'stage': 'stage0',
                                'title': 'UT stage dept0.tut0.lec0.stage0'
                            },
                        ],
                    }, {
                        'name': 'lec1',
                        'path': Ltree('dept0.tut0.lec1'),
                        'title': 'UT Lecture dept0.tut0.lec1',
                        'children': [
                            {
                                'href': '/api/stage?path=dept0.tut0.lec1.stage0',
                                'stage': 'stage0',
                                'title': 'UT stage dept0.tut0.lec1.stage0'
                            },
                        ],
                    }
                ]
            },
            {
                'name': 'lec1',
                'path': Ltree('dept0.tut1.lec1'),
                'title': 'UT Lecture dept0.tut1.lec1',
                'children': [
                    {
                        'href': '/api/stage?path=dept0.tut1.lec1.stage0',
                        'stage': 'stage0',
                        'title': 'UT stage dept0.tut1.lec1.stage0',
                    }
                ],
            }
        ]})

        out = view_subscription_list(self.request(user=self.db_studs[1]))
        self.assertEqual(out, {'children': [
            {
                'name': 'tut1',
                'path': Ltree('dept0.tut1'),
                'title': 'UT Lecture dept0.tut1',
                'children': [
                    {
                        'name': 'lec0',
                        'path': Ltree('dept0.tut1.lec0'),
                        'title': 'UT Lecture dept0.tut1.lec0',
                        'children': [
                            {
                                'href': '/api/stage?path=dept0.tut1.lec0.stage0',
                                'stage': 'stage0',
                                'title': 'UT stage dept0.tut1.lec0.stage0'
                            },
                        ],
                    }, {
                        'name': 'lec1',
                        'path': Ltree('dept0.tut1.lec1'),
                        'title': 'UT Lecture dept0.tut1.lec1',
                        'children': [
                            {
                                'href': '/api/stage?path=dept0.tut1.lec1.stage0',
                                'stage': 'stage0',
                                'title': 'UT stage dept0.tut1.lec1.stage0'
                            },
                        ],
                    }
                ]
            },
        ]})
