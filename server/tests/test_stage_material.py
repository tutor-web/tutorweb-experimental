import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank

from tutorweb_quizdb.stage.dataframe import view_stage_dataframe
from tutorweb_quizdb.stage.material import view_stage_material
from tutorweb_quizdb.material.render import MissingDataException


class ViewStageMaterialTest(RequiresMaterialBank, RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_dataframe(self):
        """When fetching, we make sure that data for questions is provided"""
        from tutorweb_quizdb import DBSession
        self.DBSession = DBSession

        # Add stages
        self.db_stages = self.create_stages(3, lec_parent='ut.ans_queue.0', stage_setting_spec_fn=lambda i: dict(
            allocation_method=dict(value='passthrough'),
            allocation_bank_name=dict(value=self.material_bank.name),
        ), material_tags_fn=lambda i: [
            'type.question',
            'ex.12',
        ])
        DBSession.flush()

        # Add another lecture to the same tutorial
        self.db_other_stages = self.create_stages(1, lec_parent='ut.ans_queue.0', stage_setting_spec_fn=lambda i: dict(
            allocation_method=dict(value='passthrough'),
            allocation_bank_name=dict(value=self.material_bank.name),
        ), material_tags_fn=lambda i: [
            'type.question',
            'ex.23',
        ])
        DBSession.flush()

        self.db_studs = self.create_students(2)
        DBSession.flush()

        # Add material
        self.mb_write_file('df/data_a.json', b'''{ "cow": "moo" }''')
        self.mb_write_file('df/data_b.json', b'''{ "pig": "oink" }''')
        self.mb_write_file('example1.q.R', b'''
# TW:TAGS=ex.12
# TW:PERMUTATIONS=2
# TW:DATAFRAMES=df/data_a.json

question <- function(permutation, data_frames) { return(list(content = paste('q1', toJSON(data_frames[['df/data_a.json']])), correct = list())) }
        ''')
        self.mb_write_file('example2.q.R', b'''
# TW:TAGS=ex.12,ex.23
# TW:PERMUTATIONS=2
# TW:DATAFRAMES=df/data_a.json

question <- function(permutation, data_frames) { return(list(content = paste('q2', toJSON(data_frames[['df/data_a.json']])), correct = list())) }
        ''')
        self.mb_write_file('example3.q.R', b'''
# TW:TAGS=ex.23
# TW:PERMUTATIONS=2
# TW:DATAFRAMES=df/data_b.json

question <- function(permutation, data_frames) { return(list(content = paste('q3', toJSON(data_frames[['df/data_b.json']])), correct = list())) }
        ''')
        self.mb_update()

        # Can't fetch yet, haven't provided data
        with self.assertRaisesRegex(MissingDataException, r'df/data_a\.json'):
            lec_1_material = view_stage_material(self.request(user=self.db_studs[0], params=dict(path=self.db_stages[0])))

        # Note df keys for convenience
        lec_2_df = view_stage_dataframe(self.request(user=self.db_studs[0], params=dict(path=self.db_other_stages[0])))
        for k in lec_2_df.keys():
            if 'cow' in lec_2_df[k]['template']:
                df_key_cow = k
            else:
                df_key_pig = k

        # Provide data, get material
        view_stage_dataframe(self.request(
            user=self.db_studs[0],
            params=dict(path=self.db_stages[0]),
            method='PUT',
            body=dict(data={
                df_key_cow: dict(cow='bessie'),
            }),
        ))
        lec_1_material = view_stage_material(self.request(user=self.db_studs[0], params=dict(path=self.db_stages[0])))
        self.assertEqual(lec_1_material['data'], {
            'example1.q.R:1:1': {'correct': [], 'tags': ['ex.12', 'type.question'], 'content': 'q1 {"cow":["bessie"]}'},
            'example1.q.R:1:2': {'correct': [], 'tags': ['ex.12', 'type.question'], 'content': 'q1 {"cow":["bessie"]}'},
            'example2.q.R:1:1': {'correct': [], 'tags': ['ex.12', 'ex.23', 'type.question'], 'content': 'q2 {"cow":["bessie"]}'},
            'example2.q.R:1:2': {'correct': [], 'tags': ['ex.12', 'ex.23', 'type.question'], 'content': 'q2 {"cow":["bessie"]}'},
        })

        # Need data_b also for other lecture
        with self.assertRaisesRegex(MissingDataException, r'df/data_b\.json'):
            lec_2_material = view_stage_material(self.request(user=self.db_studs[0], params=dict(path=self.db_other_stages[0])))
        lec_2_df = view_stage_dataframe(self.request(
            user=self.db_studs[0],
            params=dict(path=self.db_other_stages[0]),
            method='PUT',
            body=dict(data={
                df_key_cow: dict(cow='bessie'),
                df_key_pig: dict(pig='george'),
            }),
        ))
        lec_2_material = view_stage_material(self.request(user=self.db_studs[0], params=dict(path=self.db_other_stages[0])))
        self.assertEqual(lec_2_material['data'], {
            'example2.q.R:1:1': {'tags': ['ex.12', 'ex.23', 'type.question'], 'correct': [], 'content': 'q2 {"cow":["bessie"]}'},
            'example2.q.R:1:2': {'tags': ['ex.12', 'ex.23', 'type.question'], 'correct': [], 'content': 'q2 {"cow":["bessie"]}'},
            'example3.q.R:1:2': {'tags': ['ex.23', 'type.question'], 'correct': [], 'content': 'q3 {"pig":["george"]}'},
            'example3.q.R:1:1': {'tags': ['ex.23', 'type.question'], 'correct': [], 'content': 'q3 {"pig":["george"]}'},
        })

        # The other user doesn't get anything
        with self.assertRaisesRegex(MissingDataException, r'df/data_[ab]\.json'):
            lec_2_material = view_stage_material(self.request(user=self.db_studs[1], params=dict(path=self.db_other_stages[0])))
