import unittest

from pyramid.httpexceptions import HTTPForbidden

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank

from tutorweb_quizdb.material.render import view_material_render


class ViewMaterialRender(RequiresMaterialBank, RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_call(self):
        from tutorweb_quizdb import DBSession
        self.DBSession = DBSession

        # Add some students
        self.db_studs = self.create_students(
            2,
            student_group_fn=lambda i: ['accept_terms', 'admin.material_render'] if i == 0 else ['accept_terms']
        )

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

        # Student 1 can't preview by name
        with self.assertRaises(HTTPForbidden):
            view_material_render(self.request(user=self.db_studs[1], body=dict(path='example1.q.R')))

        # Student 0 tries, but didn't provide data
        out = view_material_render(self.request(user=self.db_studs[0], body=dict(
            path='example1.q.R'
        )))
        self.assertEqual(out, dict(
            dataframe_templates={'df/data_a.json': {'cow': 'moo'}},
            error='Not enough data to render question',
        ))
        out = view_material_render(self.request(user=self.db_studs[0], body=dict(
            path='example3.q.R'
        )))
        self.assertEqual(out, dict(
            dataframe_templates={'df/data_b.json': {'pig': 'oink'}},
            error='Not enough data to render question',
        ))

        # Now they did
        out = view_material_render(self.request(user=self.db_studs[0], body=dict(
            path='example1.q.R',
            student_dataframes={
                'df/data_a.json': dict(cow=1),
            },
        )))
        self.assertEqual(out, dict(
            dataframe_templates={'df/data_a.json': {'cow': 'moo'}},
            content='',
            correct=[],
            tags=['ex.12', 'type.question'],
        ))
