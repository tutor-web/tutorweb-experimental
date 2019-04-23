import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank

from tutorweb_quizdb.stage.ug_extensions import view_stage_ug_rewrite
from tutorweb_quizdb.stage.allocation import get_allocation
from tutorweb_quizdb.stage.setting import getStudentSettings
from tutorweb_quizdb.stage.answer_queue import sync_answer_queue


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
    if 'student_answer' not in d:
        d['student_answer'] = {}
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


class StageUgRewriteTest(RequiresMaterialBank, RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_call(self):
        from tutorweb_quizdb import DBSession
        self.DBSession = DBSession

        # Add stages
        self.db_stages = self.create_stages(1, lec_parent='ut.ug_extensions.0', stage_setting_spec_fn=lambda i: dict(
            allocation_method=dict(value='passthrough'),
            allocation_bank_name=dict(value=self.material_bank.name),
        ), material_tags_fn=lambda i: [
            'type.template',
            'lec050500',
        ])
        DBSession.flush()

        # Add material
        self.mb_write_file('template1.t.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:PERMUTATIONS=1

question <- function(permutation, data_frames) { return(list(content = '', correct = list())) }
        ''')
        self.mb_update()

        self.db_studs = self.create_students(2)
        DBSession.flush()

        # Templates should get their own sequence ID
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[0]), [
            aq_dict(uri='template1.t.R:1:1', time_end=1010, correct=None, student_answer=dict(text="2"), review=None),
        ], 0)
        self.assertEqual(out, [
            aq_dict(uri='template1.t.R:1:10', time_end=1010, correct=None, student_answer=dict(text="2"), review=None),
        ])

        # Other students not allowed to mark as superseded, nothing changes
        with self.assertRaisesRegex(ValueError, 'Expected to find one answer, not 0'):
            out = view_stage_ug_rewrite(self.request(user=self.db_studs[1], params=dict(
                uri='template1.t.R:1:10',
                path=self.db_stages[0],
            )))
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[0]), [], 0)
        self.assertEqual(out, [
            aq_dict(uri='template1.t.R:1:10', time_end=1010, correct=None, student_answer=dict(text="2"), review=None),
        ])

        # Mark this question as superseded, we get back the question info
        out = view_stage_ug_rewrite(self.request(user=self.db_studs[0], params=dict(
            uri='template1.t.R:1:10',
            path=self.db_stages[0],
        )))
        self.assertEqual(out, dict(
            uri='template1.t.R:1:1',  # NB: We get the URI of the template, not the question
            student_answer=dict(text="2"),
        ))

        # If we check again, we see it's superseded
        (out, additions) = sync_answer_queue(get_alloc(self.db_stages[0], self.db_studs[0]), [], 0)
        self.assertEqual(out, [
            aq_dict(uri='template1.t.R:1:10', time_end=1010, correct=False, student_answer=dict(text="2"), review={"superseded": True}),
        ])
