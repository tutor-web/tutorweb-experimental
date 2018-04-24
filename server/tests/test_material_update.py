import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank


class ViewMaterialUpdateTest(RequiresPyramid, RequiresMaterialBank, RequiresPostgresql, unittest.TestCase):
    def call_view(self):
        from tutorweb_quizdb.material.update import view_material_update
        from tutorweb_quizdb import DBSession, Base

        request = self.request(settings={'tutorweb.material_bank': self.material_bank.name})
        out = view_material_update(request)
        self.assertEqual(out, None)

        out = {}
        for ms in DBSession.query(Base.classes.materialsource):
            out[ms.path] = (
                ms.revision,
                ms.material_tags,
            )
        return out

    def test_update(self):
        # Empty material bank has nothing in it
        out = self.call_view()
        self.assertEqual(out, {
        })

        # Add a file, becomes available
        self.mb_write_file('example.q.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:QUESTIONS=100
# TW:DATAFRAMES=agelength
        ''')
        self.assertEqual(self.call_view(), {
            'example.q.R': ('(untracked)+1', ['math099', 'Q-0990t0', 'lec050500', 'type.question']),
        })

        # Add a second file, also available
        self.mb_write_file('extra/another.q.R', b'''# TW:TAGS=math1234''')
        self.assertEqual(self.call_view(), {
            'example.q.R': ('(untracked)+1', ['math099', 'Q-0990t0', 'lec050500', 'type.question']),
            'extra/another.q.R': ('(untracked)+1', ['math1234', 'type.question']),
        })

        # Re-writing first doesn't change anything
        self.mb_write_file('example.q.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:QUESTIONS=100
# TW:DATAFRAMES=agelength
        ''')
        self.assertEqual(self.call_view(), {
            'example.q.R': ('(untracked)+1', ['math099', 'Q-0990t0', 'lec050500', 'type.question']),
            'extra/another.q.R': ('(untracked)+1', ['math1234', 'type.question']),
        })

        # ...but new content does
        self.mb_write_file('example.q.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,hello.mum
# TW:QUESTIONS=100
# TW:DATAFRAMES=agelength
        ''')
        self.assertEqual(self.call_view(), {
            'example.q.R': ('(untracked)+2', ['math099', 'Q-0990t0', 'lec050500', 'hello.mum', 'type.question']),
            'extra/another.q.R': ('(untracked)+1', ['math1234', 'type.question']),
        })

        # Reverting back creates another new version
        self.mb_write_file('example.q.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:QUESTIONS=100
# TW:DATAFRAMES=agelength
        ''')
        self.assertEqual(self.call_view(), {
            'example.q.R': ('(untracked)+3', ['math099', 'Q-0990t0', 'lec050500', 'type.question']),
            'extra/another.q.R': ('(untracked)+1', ['math1234', 'type.question']),
        })
