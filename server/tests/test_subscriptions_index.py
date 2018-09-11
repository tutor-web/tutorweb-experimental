import unittest

from sqlalchemy_utils import Ltree

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.subscriptions.index import add_syllabus, subscription_add, subscription_remove, view_subscription_list
from tutorweb_quizdb.subscriptions.available import view_subscription_available


class AddSyllabusTest(unittest.TestCase):
    maxDiff = None

    def test_withsamename(self):
        """Adding items at same level with same name shouldn't cause a problem"""
        out_root = dict(children=[])

        add_syllabus(out_root, Ltree('math.101.0'), dict(title='hi'), 2)
        add_syllabus(out_root, Ltree('math.101.0.1'), dict(title='hi l1'), 2)
        add_syllabus(out_root, Ltree('math.101.0.2'), dict(title='hi l2'), 2)
        add_syllabus(out_root, Ltree('math.612.0'), dict(title='hello'), 2)
        add_syllabus(out_root, Ltree('math.612.0.1'), dict(title='hello 1'), 2)
        self.assertEqual(out_root, dict(children=[
            {
                'path': Ltree('math.101.0'), 'title': 'hi',
                'children': [
                    {'path': Ltree('math.101.0.1'), 'title': 'hi l1', 'children': []},
                    {'path': Ltree('math.101.0.2'), 'title': 'hi l2', 'children': []},
                ]
            },
            {
                'path': Ltree('math.612.0'), 'title': 'hello',
                'children': [
                    {'path': Ltree('math.612.0.1'), 'title': 'hello 1', 'children': []},
                ]
            },
        ]))


class SubscriptionsListTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def setUp(self):
        super(SubscriptionsListTest, self).setUp()

        from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
        self.DBSession = DBSession

        lecture_paths = [
            'dept0',
            'dept0.tut0',
            'dept0.tut0.lec0',
            'dept0.tut0.lec1',
            'dept0.tut1',
            'dept0.tut1.lec0',
            'dept0.tut1.lec1',
            'dept1',
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
        self.db_studs = self.create_students(
            3,
            student_group_fn=lambda i: ['accept_terms', 'super_secret'] if i == 0 else ['accept_terms']
        )

    def test_call(self):
        from tutorweb_quizdb import DBSession

        # make some subscriptions
        subscription_add(self.db_studs[0], Ltree('dept0.tut0'))
        subscription_add(self.db_studs[0], Ltree('dept0.tut1.lec1'))
        subscription_add(self.db_studs[1], Ltree('dept0.tut1'))
        DBSession.flush()

        out0_pre_secret = view_subscription_list(self.request(user=self.db_studs[0]))
        self.assertEqual(out0_pre_secret, {'children': [
            {
                'path': Ltree('dept0.tut0'),
                'title': 'UT Lecture dept0.tut0',
                'children': [
                    {
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
                'path': Ltree('dept0.tut1'),
                'title': 'UT Lecture dept0.tut1',
                'children': [
                    {
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

        # Make dept0.tut1.lec1 super-secret, only stud0 can see it
        self.db_lecs['dept0.tut1.lec1'].requires_group_id = [g.id for g in self.db_studs[0].groups if g.name == 'super_secret'][0]
        DBSession.flush()

        out0_post_secret = view_subscription_list(self.request(user=self.db_studs[0]))
        self.assertEqual(out0_post_secret, out0_pre_secret)

        out = view_subscription_list(self.request(user=self.db_studs[1]))
        self.assertEqual(out, {'children': [
            {
                'path': Ltree('dept0.tut1'),
                'title': 'UT Lecture dept0.tut1',
                'children': [
                    {
                        'path': Ltree('dept0.tut1.lec0'),
                        'title': 'UT Lecture dept0.tut1.lec0',
                        'children': [
                            {
                                'href': '/api/stage?path=dept0.tut1.lec0.stage0',
                                'stage': 'stage0',
                                'title': 'UT stage dept0.tut1.lec0.stage0'
                            },
                        ],
                    }
                ]
            },
        ]})

        # Repeatedly adding isn't a problem
        subscription_add(self.db_studs[0], Ltree('dept0.tut0'))
        subscription_add(self.db_studs[0], Ltree('dept0.tut1.lec1'))
        subscription_add(self.db_studs[1], Ltree('dept0.tut1'))
        DBSession.flush()

        # Remove subscription from dept0.tut1.lec1, it disappears
        subscription_remove(self.db_studs[0], Ltree('dept0.tut1.lec1'))
        out = view_subscription_list(self.request(user=self.db_studs[0]))
        self.assertEqual(out, {'children': [
            {
                'path': Ltree('dept0.tut0'),
                'title': 'UT Lecture dept0.tut0',
                'children': [
                    {
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
        ]})

        # Still available though
        out = view_subscription_available(self.request(user=self.db_studs[0]))
        self.assertEqual(out, {'children': [
            {
                'path': Ltree('dept0'),
                'subscribed': None,
                'supporting_material_href': None,
                'title': 'UT Lecture dept0',
                'children': [
                    {
                        'path': Ltree('dept0.tut0'),
                        'subscribed': Ltree('dept0.tut0'),
                        'supporting_material_href': None,
                        'title': 'UT Lecture dept0.tut0',
                        'children': [
                            {
                                'path': Ltree('dept0.tut0.lec0'),
                                'subscribed': Ltree('dept0.tut0'),  # NB: This is the root of our subscription
                                'supporting_material_href': 'http://wikipedia.org/',
                                'title': 'UT Lecture dept0.tut0.lec0',
                                'children': [],
                            }, {
                                'path': Ltree('dept0.tut0.lec1'),
                                'subscribed': Ltree('dept0.tut0'),  # NB: This is the root of our subscription
                                'supporting_material_href': None,
                                'title': 'UT Lecture dept0.tut0.lec1',
                                'children': [],
                            },
                        ],
                    }, {
                        'path': Ltree('dept0.tut1'),
                        'subscribed': None,
                        'supporting_material_href': None,
                        'title': 'UT Lecture dept0.tut1',
                        'children': [
                            {
                                'path': Ltree('dept0.tut1.lec0'),
                                'subscribed': None,
                                'supporting_material_href': None,
                                'title': 'UT Lecture dept0.tut1.lec0',
                                'children': [],
                            }, {
                                'path': Ltree('dept0.tut1.lec1'),
                                'subscribed': None,
                                'supporting_material_href': None,
                                'title': 'UT Lecture dept0.tut1.lec1',
                                'children': [],
                            },
                        ],
                    },
                ],
            }, {
                'path': Ltree('dept1'),
                'subscribed': None,
                'supporting_material_href': None,
                'title': 'UT Lecture dept1',
                'children': [
                    {
                        'path': Ltree('dept1.tut2'),
                        'subscribed': None,
                        'supporting_material_href': None,
                        'title': 'UT Lecture dept1.tut2',
                        'children': [
                            {
                                'path': Ltree('dept1.tut2.lec0'),
                                'subscribed': None,
                                'supporting_material_href': None,
                                'title': 'UT Lecture dept1.tut2.lec0',
                                'children': [],
                            }, {
                                'path': Ltree('dept1.tut2.lec1'),
                                'subscribed': None,
                                'supporting_material_href': None,
                                'title': 'UT Lecture dept1.tut2.lec1',
                                'children': [],
                            },
                        ]
                    }
                ],
            }
        ]})
