import random
import unittest

from sqlalchemy_utils import Ltree

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank

from tutorweb_quizdb.stage.allocation import get_allocation
from tutorweb_quizdb.stage.setting import getStudentSettings
from tutorweb_quizdb.stage.answer_queue import sync_answer_queue


def get_alloc(db_stage, db_student):
    """Get settings & allocation in one step"""
    settings = getStudentSettings(db_stage, db_student)
    alloc = get_allocation(settings, db_stage, db_student)
    return alloc


class SyncAnswerQueueTest(RequiresMaterialBank, RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def setUp(self):
        super(SyncAnswerQueueTest, self).setUp()

        from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST
        from tutorweb_quizdb import models
        self.DBSession = DBSession

        # Add stage
        lec_name = 'lec_%d' % random.randint(1000000, 9999999)
        db_lec = Base.classes.syllabus(host_id=ACTIVE_HOST, path=Ltree(lec_name), title=lec_name)
        DBSession.add(db_lec)
        self.db_stages = [Base.classes.stage(
            syllabus=db_lec,
            stage_name='stage%d' % i, version=0,
            title='UT stage %s' % i,
            stage_setting_spec=dict(
                allocation_method=dict(value='passthrough'),
                allocation_bank_name=dict(value=self.material_bank.name),
            )
        ) for i in [0, 1, 2]]
        for i in [0, 1, 2]:
            DBSession.add(self.db_stages[i])
        DBSession.flush()
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
            dict(client_id='01', uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=None, synced=True),
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
            dict(client_id='01', uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes"), synced=True),
            dict(client_id='01', uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=None, synced=True),
        ])
        self.assertEqual(additions, 0)

        # Can add items with differing time_offsets
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='example2.q.R:1', time_start=1000, time_end=1010, correct=True, grade_after=0.1, student_answer=dict(answer="late"), review=None),
        ], 300)
        self.assertEqual(out, [
            dict(client_id='01', uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes"), synced=True),
            dict(client_id='01', uri='example2.q.R:1', time_start=1000, time_end=1010, time_offset=300, correct=True, grade_after=0.1, student_answer=dict(answer="late"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=None, synced=True),
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
            dict(client_id='01', uri='example1.q.R:6', time_start=1000, time_end=1005, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes"), synced=True),
            dict(client_id='01', uri='example2.q.R:1', time_start=1000, time_end=1010, time_offset=300, correct=True, grade_after=0.1, student_answer=dict(answer="late"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:7', time_start=1010, time_end=1015, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:8', time_start=1020, time_end=1025, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3"), review=None, synced=True),
        ])
        self.assertEqual(additions, 3)

        # Templates should get their own sequence ID
        alloc = get_alloc(self.db_stages[0], self.db_studs[1])
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='template1.t.R:1', time_start=1000, time_end=1010, correct=True, grade_after=0.1, student_answer=dict(text="2")),
            dict(client_id='01', uri='template1.t.R:1', time_start=1010, time_end=1020, correct=True, grade_after=0.1, student_answer=dict(text="3")),
        ], 0)
        self.assertEqual(out, [
            dict(client_id='01', uri='template1.t.R:10', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(text="2"), review=None, synced=True),
            dict(client_id='01', uri='template1.t.R:11', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(text="3"), review=None, synced=True),
        ])
        self.assertEqual(additions, 2)
        (out, additions) = sync_answer_queue(alloc, [
            dict(client_id='01', uri='template1.t.R:1', time_start=1020, time_end=1030, correct=True, grade_after=0.1, student_answer=dict(text="4")),
        ], 0)
        self.assertEqual(out, [
            dict(client_id='01', uri='template1.t.R:10', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(text="2"), review=None, synced=True),
            dict(client_id='01', uri='template1.t.R:11', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(text="3"), review=None, synced=True),
            dict(client_id='01', uri='template1.t.R:12', time_start=1020, time_end=1030, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(text="4"), review=None, synced=True),
        ])
        self.assertEqual(additions, 1)

        # We can still get student 0's work, after this diversion to student 1
        alloc = get_alloc(self.db_stages[0], self.db_studs[0])
        (out, additions) = sync_answer_queue(alloc, [
        ], 0)
        self.assertEqual(out, [
            dict(client_id='01', uri='example1.q.R:6', time_start=1000, time_end=1005, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:4', time_start=1000, time_end=1010, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=dict(hard="yes"), synced=True),
            dict(client_id='01', uri='example2.q.R:1', time_start=1000, time_end=1010, time_offset=300, correct=True, grade_after=0.1, student_answer=dict(answer="late"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:7', time_start=1010, time_end=1015, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:5', time_start=1010, time_end=1020, time_offset=0, correct=True, grade_after=0.1, student_answer=dict(answer="2"), review=None, synced=True),
            dict(client_id='01', uri='example1.q.R:8', time_start=1020, time_end=1025, time_offset=0, correct=True, grade_after=0.2, student_answer=dict(answer="3"), review=None, synced=True),
        ])
        self.assertEqual(additions, 0)

        # ... and no work in second stage
        alloc = get_alloc(self.db_stages[1], self.db_studs[0])
        (out, additions) = sync_answer_queue(alloc, [
        ], 0)
        self.assertEqual(out, [
        ])
        self.assertEqual(additions, 0)
