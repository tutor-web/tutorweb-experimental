import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank

from tutorweb_quizdb.stage.dataframe import view_stage_dataframe


class ViewStageDataFrameTest(RequiresMaterialBank, RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_call(self):
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

        self.db_studs = self.create_students(1)
        DBSession.flush()

        # Add material
        self.mb_write_file('df/data_a.json', b'''{ "cow": "moo" }''')
        self.mb_write_file('df/data_b.json', b'''{ "pig": "oink" }''')
        self.mb_write_file('example1.q.R', b'''
# TW:TAGS=ex.12
# TW:PERMUTATIONS=10
# TW:DATAFRAMES=df/data_a.json

question <- function(permutation, data_frames) { return(list(content = '', correct = list())) }
        ''')
        self.mb_write_file('example2.q.R', b'''
# TW:TAGS=ex.12,ex.23
# TW:PERMUTATIONS=10
# TW:DATAFRAMES=df/data_a.json

question <- function(permutation, data_frames) { return(list(content = '', correct = list())) }
        ''')
        self.mb_write_file('example3.q.R', b'''
# TW:TAGS=ex.23
# TW:PERMUTATIONS=10
# TW:DATAFRAMES=df/data_b.json

question <- function(permutation, data_frames) { return(list(content = '', correct = list())) }
        ''')
        self.mb_update()

        # Fetch list of data frames for first lecture
        lec_1_df = view_stage_dataframe(self.request(user=self.db_studs[0], params=dict(path=self.db_stages[0])))
        self.assertEqual(len(lec_1_df), 1)
        self.assertIn(dict(template=dict(cow='moo'), data=None), lec_1_df.values())

        # Fetch list of data frames for second lecture
        lec_2_df = view_stage_dataframe(self.request(user=self.db_studs[0], params=dict(path=self.db_other_stages[0])))
        self.assertEqual(len(lec_2_df), 2)
        self.assertIn(dict(template=dict(cow='moo'), data=None), list(lec_2_df.values()))
        self.assertIn(dict(template=dict(pig='oink'), data=None), list(lec_2_df.values()))

        # Note what the keys are for convenience
        lec_1_key_cow = list(lec_1_df.keys())[0]
        for k in lec_2_df.keys():
            if 'cow' in lec_2_df[k]['template']:
                lec_2_key_cow = k
            else:
                lec_2_key_pig = k

        # The 2 instances of df/data_a.json share the same key (whatever it is)
        self.assertEqual(lec_1_key_cow, lec_2_key_cow)

        # Set required data for first lecture
        lec_1_df = view_stage_dataframe(self.request(
            user=self.db_studs[0],
            params=dict(path=self.db_stages[0]),
            method='PUT',
            body=dict(data={
                lec_1_key_cow: dict(cow='bessie'),
                lec_2_key_pig: dict(pig='george'),  # NB: This isn't part of lec1, gets ignored
            }),
        ))
        self.assertEqual(lec_1_df, {
            lec_1_key_cow: dict(template=dict(cow='moo'), data=dict(cow='bessie')),
        })

        # Can fetch the data from the second lecture
        lec_2_df = view_stage_dataframe(self.request(user=self.db_studs[0], params=dict(path=self.db_other_stages[0])))
        self.assertEqual(lec_2_df, {
            lec_2_key_cow: dict(template=dict(cow='moo'), data=dict(cow='bessie')),
            lec_2_key_pig: dict(template=dict(pig='oink'), data=None),  # NB: No data set
        })

        # Update both dataframes of second lecture
        lec_2_df = view_stage_dataframe(self.request(
            user=self.db_studs[0],
            params=dict(path=self.db_other_stages[0]),
            method='PUT',
            body=dict(data={
                lec_2_key_cow: dict(cow='freda'),
                lec_2_key_pig: dict(pig='gary'),
            }),
        ))
        self.assertEqual(lec_2_df, {
            lec_2_key_cow: dict(template=dict(cow='moo'), data=dict(cow='freda')),
            lec_2_key_pig: dict(template=dict(pig='oink'), data=dict(pig='gary')),
        })

        # Updates also visible in lec1
        lec_1_df = view_stage_dataframe(self.request(user=self.db_studs[0], params=dict(path=self.db_stages[0])))
        self.assertEqual(lec_1_df, {
            lec_1_key_cow: dict(template=dict(cow='moo'), data=dict(cow='freda')),
        })

        # Also in lec2 again
        lec_2_df = view_stage_dataframe(self.request(user=self.db_studs[0], params=dict(path=self.db_other_stages[0])))
        self.assertEqual(lec_2_df, {
            lec_2_key_cow: dict(template=dict(cow='moo'), data=dict(cow='freda')),
            lec_2_key_pig: dict(template=dict(pig='oink'), data=dict(pig='gary')),
        })
