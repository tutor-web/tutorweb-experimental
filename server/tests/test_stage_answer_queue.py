import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank

from tutorweb_quizdb.stage.allocation import get_allocation
from tutorweb_quizdb.stage.setting import getStudentSettings
from tutorweb_quizdb.stage.answer_queue import sync_answer_queue, request_review


def aq_dict(**d):
    """Fill in the boring bits of an answer queue entry"""
    if 'ug_reviews' not in d:
        d['ug_reviews'] = []
    d['synced'] = True
    if 'client_id' not in d:
        d['client_id'] = '01'
    if 'review' not in d:
        d['review'] = None
    if 'time_start' not in d:
        d['time_start'] = d['time_end'] - 10
    if 'time_offset' not in d:
        d['time_offset'] = 0
    if 'correct' not in d:
        d['correct'] = True
    if 'grade_after' not in d:
        d['grade_after'] = 0.1
    if 'mark' not in d:
        d['mark'] = 0
    return d


def get_alloc(db_stage, db_student):
    """Get settings & allocation in one step"""
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)
    return alloc


class SyncAnswerQueueTest(RequiresMaterialBank, RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def setUp(self):
        super(SyncAnswerQueueTest, self).setUp()

        from tutorweb_quizdb import DBSession
        self.DBSession = DBSession

        # Add stage
        self.db_stages = self.create_stages(3, stage_setting_spec_fn=lambda i: dict(
            allocation_method=dict(value='passthrough'),
            allocation_bank_name=dict(value=self.material_bank.name),
            ugreview_minreviews=dict(value=3),
            ugreview_captrue=dict(value=50),
            ugreview_capfalse=dict(value=-50),
        ), material_tags_fn=lambda i: [
            'type.template',
            'lec050500',
        ])
        DBSession.flush()

        self.db_studs = self.create_students(4)
        DBSession.flush()

        # Add material
        self.mb_write_file('example1.q.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:PERMUTATIONS=10
# TW:DATAFRAMES=agelength
        ''')
        self.mb_write_file('example2.q.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:PERMUTATIONS=10
# TW:DATAFRAMES=agelength
        ''')
        self.mb_write_file('template1.t.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:PERMUTATIONS=1
        ''')
        self.mb_update()

    def test_call(self):
        # Can sync empty answer queue with empty
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[0]), [], 0)
        self.assertEqual(out, [])
        self.assertEqual(additions, 0)

        # Add some items into the queue, get them back again. Entries without time_end are ignored
        alloc = get_alloc(self.db_stages[0], self.db_studs[0])
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='example1.q.R:4', time_start=1000, time_end=1010, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
            dict(client_id='01', uri='example1.q.R:5', time_start=1010, time_end=1020, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
            dict(client_id='01', uri='example1.q.R:9', time_start=1090),
        ], 0)
        self.assertEqual(out, [
            aq_dict(uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
            aq_dict(uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
        ])
        self.assertEqual(additions, 2)

        # Questions with invalid URIs are complained about
        alloc = get_alloc(self.db_stages[0], self.db_studs[0])
        with self.assertRaisesRegex(ValueError, 'parpparpparp'):
            (out, additions) = sync_answer_queue(alloc, [
                dict(client_id='01', uri='parpparpparp', time_start=1000, time_end=1007, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
            ], 0)

        # Can only add reviews to existing items
        alloc = get_alloc(self.db_stages[0], self.db_studs[0])
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='example1.q.R:4', time_start=1000, time_end=1010, correct=True, grade_after=0.1, student_answer=dict(answer="ignored"), review=dict(hard="yes")),
        ], 0)
        self.assertEqual(out, [
            aq_dict(uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes")),
            aq_dict(uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
        ])
        self.assertEqual(additions, 0)

        # Can add items with differing time_offsets
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='example2.q.R:1', time_start=1000, time_end=1010, correct=True, grade_after=0.1, student_answer=dict(answer="late"), review=None),
        ], 300)
        self.assertEqual(out, [
            aq_dict(uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes")),
            aq_dict(uri='example2.q.R:1', time_start=1000, time_end=1010, time_offset=300, correct=True, grade_after=0.1, student_answer=dict(answer="late")),
            aq_dict(uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
        ])
        self.assertEqual(additions, 1)

        # Can interleave new material, get back everything
        alloc = get_alloc(self.db_stages[0], self.db_studs[0])
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='example1.q.R:6', time_start=1000, time_end=1005, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
            dict(client_id='01', uri='example1.q.R:7', time_start=1010, time_end=1015, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
            dict(client_id='01', uri='example1.q.R:8', time_start=1020, time_end=1025, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
        ], 0)
        self.assertEqual(out, [
            aq_dict(uri='example1.q.R:6', time_start=1000, time_end=1005, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
            aq_dict(uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes")),
            aq_dict(uri='example2.q.R:1', time_start=1000, time_end=1010, time_offset=300, correct=True, grade_after=0.1, student_answer=dict(answer="late")),
            aq_dict(uri='example1.q.R:7', time_start=1010, time_end=1015, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
            aq_dict(uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
            aq_dict(uri='example1.q.R:8', time_start=1020, time_end=1025, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
        ])
        self.assertEqual(additions, 3)

        # Templates should get their own sequence ID
        alloc = get_alloc(self.db_stages[0], self.db_studs[1])
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='template1.t.R:1', time_start=1000, time_end=1010, correct=None, grade_after=0.1, student_answer=dict(text="2")),
            dict(client_id='01', uri='template1.t.R:1', time_start=1010, time_end=1020, correct=None, grade_after=0.1, student_answer=dict(text="3")),
        ], 0)
        self.assertEqual(out, [
            aq_dict(uri='template1.t.R:10', time_start=1000, time_end=1010, time_offset=0, correct=None, grade_after=0.1, student_answer=dict(text="2"), review=None),
            aq_dict(uri='template1.t.R:11', time_start=1010, time_end=1020, time_offset=0, correct=None, grade_after=0.1, student_answer=dict(text="3"), review=None),
        ])
        self.assertEqual(additions, 2)
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='template1.t.R:1', time_start=1020, time_end=1030, correct=None, grade_after=0.1, student_answer=dict(text="4")),
        ], 0)
        self.assertEqual(out, [
            # NB: correct has been rewritten back to none, since there's no review
            aq_dict(uri='template1.t.R:10', time_start=1000, time_end=1010, time_offset=0, correct=None, grade_after=0.1, student_answer=dict(text="2"), review=None, ug_reviews=[]),
            aq_dict(uri='template1.t.R:11', time_start=1010, time_end=1020, time_offset=0, correct=None, grade_after=0.1, student_answer=dict(text="3"), review=None, ug_reviews=[]),
            aq_dict(uri='template1.t.R:12', time_start=1020, time_end=1030, time_offset=0, correct=None, grade_after=0.1, student_answer=dict(text="4"), review=None, ug_reviews=[]),
        ])
        self.assertEqual(additions, 1)

        # Request review lets everyone bar student 1 review stuff
        self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[0])), [
            dict(uri='template1.t.R:10'),
            dict(uri='template1.t.R:11'),
            dict(uri='template1.t.R:12'),
        ])
        self.assertEqual(request_review(get_alloc(self.db_stages[0], self.db_studs[1])), dict())
        self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[2])), [
            dict(uri='template1.t.R:10'),
            dict(uri='template1.t.R:11'),
            dict(uri='template1.t.R:12'),
        ])
        self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[3])), [
            dict(uri='template1.t.R:10'),
            dict(uri='template1.t.R:11'),
            dict(uri='template1.t.R:12'),
        ])

        # student 0 can review student 1's work, we tell student 1 about it
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[0]), [
            aq_dict(uri='template1.t.R:10', time_end=1130, student_answer=dict(choice="a2"), review=dict(comments="Absolutely **terrible**", content=-12, presentation=-12)),
            aq_dict(uri='template1.t.R:11', time_end=1131, student_answer=dict(choice="a2"), review=dict(comments="*nice*", content=12, presentation=12)),
        ], 0)
        self.assertEqual(out[-2:], [
            aq_dict(uri='template1.t.R:10', time_end=1130, student_answer=dict(choice="a2"), review=dict(comments="Absolutely **terrible**", content=-12, presentation=-12)),
            aq_dict(uri='template1.t.R:11', time_end=1131, student_answer=dict(choice="a2"), review=dict(comments="*nice*", content=12, presentation=12)),
        ])
        self.assertEqual(additions, 2)
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[1]), [], 0)
        self.assertEqual(out, [
            aq_dict(uri='template1.t.R:10', time_end=1010, correct=None, mark=-8.0, student_answer=dict(text="2"), review=None, ug_reviews=[
                dict(comments='<p>Absolutely <strong>terrible</strong></p>', content=-12, presentation=-12, mark=-24),
            ]),
            aq_dict(uri='template1.t.R:11', time_end=1020, correct=None, mark=8.0, student_answer=dict(text="3"), review=None, ug_reviews=[
                dict(comments="<p><em>nice</em></p>", content=12, presentation=12, mark=24),
            ]),
            aq_dict(uri='template1.t.R:12', time_end=1030, correct=None, student_answer=dict(text="4"), review=None, ug_reviews=[]),
        ])

        # student 0 loses the ability to review 10 and 11
        self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[0])), [
            dict(uri='template1.t.R:12'),
        ])
        self.assertEqual(request_review(get_alloc(self.db_stages[0], self.db_studs[1])), dict())
        self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[2])), [
            dict(uri='template1.t.R:10'),
            dict(uri='template1.t.R:11'),
            dict(uri='template1.t.R:12'),
        ])

        # student 2 gives similar reviews, pushes system over the edge to marking them
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[2]), [
            aq_dict(uri='template1.t.R:10', time_end=1132, student_answer=dict(choice="a2"), review=dict(comments="Bad", content=-24, presentation=-300)),
            aq_dict(uri='template1.t.R:11', time_end=1133, student_answer=dict(choice="a2"), review=dict(comments="Good", content=24, presentation=300)),
        ], 0)
        self.assertEqual(out[-2:], [
            aq_dict(uri='template1.t.R:10', time_end=1132, student_answer=dict(choice="a2"), review=dict(comments="Bad", content=-24, presentation=-300)),
            aq_dict(uri='template1.t.R:11', time_end=1133, student_answer=dict(choice="a2"), review=dict(comments="Good", content=24, presentation=300)),
        ])
        self.assertEqual(additions, 2)
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[1]), [], 0)
        self.assertEqual(out, [
            aq_dict(uri='template1.t.R:10', time_end=1010, correct=False, mark=-116.0, student_answer=dict(text="2"), review=None, ug_reviews=[
                dict(comments='<p>Absolutely <strong>terrible</strong></p>', content=-12, presentation=-12, mark=-24),
                dict(comments="<p>Bad</p>", content=-24, presentation=-300, mark=-324),
            ]),
            aq_dict(uri='template1.t.R:11', time_end=1020, correct=True, mark=116.0, student_answer=dict(text="3"), review=None, ug_reviews=[
                dict(comments="<p><em>nice</em></p>", content=12, presentation=12, mark=24),
                dict(comments="<p>Good</p>", content=24, presentation=300, mark=324),
            ]),
            aq_dict(uri='template1.t.R:12', time_end=1030, correct=None, student_answer=dict(text="4"), review=None, ug_reviews=[]),
        ])

        # Do this a few times to cope with random-ness
        for i in range(10):
            # student 2 loses the ability to review 10 and 11
            self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[0])), [
                dict(uri='template1.t.R:12'),
            ])
            self.assertEqual(request_review(get_alloc(self.db_stages[0], self.db_studs[1])), dict())
            self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[2])), [
                dict(uri='template1.t.R:12'),
            ])
            # Student 3 does too, since these are now marked
            self.assertIn(request_review(get_alloc(self.db_stages[0], self.db_studs[3])), [
                dict(uri='template1.t.R:12'),
            ])

        # Student 1 marks question as superseded, still gets review output
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[1]), [
            dict(client_id='01', uri='template1.t.R:1', time_start=1000, time_end=1010, correct=None, grade_after=0.1, student_answer=dict(text="2"), review=dict(superseded=True)),
        ], 0)
        self.assertEqual(out[0:1], [
            aq_dict(uri='template1.t.R:10', time_end=1010, correct=False, mark=-99, student_answer=dict(text="2"), review=dict(superseded=True), ug_reviews=[
                dict(comments='<p>Absolutely <strong>terrible</strong></p>', content=-12, presentation=-12, mark=-24),
                dict(comments="<p>Bad</p>", content=-24, presentation=-300, mark=-324),
            ]),
        ])

        # We can still get student 0's work, after this diversion to student 1
        alloc = get_alloc(self.db_stages[0], self.db_studs[0])
        (out, additions) = sync_answer_queue(alloc, [
        ], 0)
        self.assertEqual(out, [
            aq_dict(uri='example1.q.R:6', time_start=1000, time_end=1005, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
            aq_dict(uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes")),
            aq_dict(uri='example2.q.R:1', time_start=1000, time_end=1010, time_offset=300, correct=True, grade_after=0.1, student_answer=dict(answer="late")),
            aq_dict(uri='example1.q.R:7', time_start=1010, time_end=1015, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
            aq_dict(uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2")),
            aq_dict(uri='example1.q.R:8', time_start=1020, time_end=1025, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3")),
            aq_dict(uri='template1.t.R:10', time_end=1130, student_answer=dict(choice="a2"), review=dict(comments="Absolutely **terrible**", content=-12, presentation=-12)),
            aq_dict(uri='template1.t.R:11', time_end=1131, student_answer=dict(choice="a2"), review=dict(comments="*nice*", content=12, presentation=12)),
        ])
        self.assertEqual(additions, 0)

        # ... and no work in second stage
        alloc = get_alloc(self.db_stages[1], self.db_studs[0])
        (out, additions) = sync_answer_queue(alloc, [
        ], 0)
        self.assertEqual(out, [
        ])
        self.assertEqual(additions, 0)
