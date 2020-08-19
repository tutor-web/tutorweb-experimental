import unittest
import unittest.mock

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.syllabus.add import lec_import, multiple_lec_import
from tutorweb_quizdb.subscriptions.available import view_subscription_available


class MultipleLecImportTest(unittest.TestCase):
    maxDiff = None

    @unittest.mock.patch('tutorweb_quizdb.syllabus.add.lec_import')
    def test_single_lecture(self, mocked_lec_import):
        """A single lecture gets passed straight through"""
        lec = dict(
            path="math.612.0",
            titles=["Math Department", "CCAS", "Numbers"],
            lectures=[
                ["lecture110", "Numbers"],
                ["lecture120", "Data vectors"],
                ["lecture130", "More on algebra"],
            ],
            stage_template=[
                dict(name="stage0", title="Answer questions", material_tags=[{"path": 1}, "type.question"]),
                dict(name="stage1", title="Write questions", material_tags=[{"path": 1}, "type.template"]),
            ],
        )
        multiple_lec_import(lec)
        mocked_lec_import.assert_called_once_with(lec)

    @unittest.mock.patch('tutorweb_quizdb.syllabus.add.lec_import')
    def test_multiple_lecture(self, mocked_lec_import):
        """A single lecture gets passed straight through"""
        lec1 = dict(
            path="math.612.0",
            titles=["Math Department", "CCAS", "Numbers"],
            lectures=[
                ["lecture110", "Numbers"],
                ["lecture120", "Data vectors"],
                ["lecture130", "More on algebra"],
            ],
            stage_template=[
                dict(name="stage0", title="Answer questions", material_tags=[{"path": 1}, "type.question"]),
                dict(name="stage1", title="Write questions", material_tags=[{"path": 1}, "type.template"]),
            ],
        )
        lec2 = dict(
            path="class.ui.612",
            titles=["Class", "UI", "CCAS"],
            lectures=["lecture101", "Everything"],
        )
        lec3 = dict(
            titles=["Class", "UI", "CCASsss"],
        )
        multiple_lec_import([lec1, lec2, lec3])

        self.assertEqual([x[0][0] for x in mocked_lec_import.call_args_list], [
            # First lec1 is imported
            lec1,
            # Overrides portions of lec1
            dict(
                path="class.ui.612",
                titles=["Class", "UI", "CCAS"],
                lectures=["lecture101", "Everything"],
                stage_template=[
                    dict(name="stage0", title="Answer questions", material_tags=[{"path": 1}, "type.question"]),
                    dict(name="stage1", title="Write questions", material_tags=[{"path": 1}, "type.template"]),
                ],
            ),
            # Elements from both lec1 and lec2
            dict(
                path="class.ui.612",
                titles=["Class", "UI", "CCASsss"],
                lectures=["lecture101", "Everything"],
                stage_template=[
                    dict(name="stage0", title="Answer questions", material_tags=[{"path": 1}, "type.question"]),
                    dict(name="stage1", title="Write questions", material_tags=[{"path": 1}, "type.template"]),
                ],
            ),
        ])


class LecImportTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_call(self):
        from tutorweb_quizdb import DBSession
        self.DBSession = DBSession

        (stud, clairvoyant) = self.create_students(2, student_group_fn=lambda i: ['accept_terms', 'admin.deleted'] if i == 1 else ['accept_terms'])

        def simple_tree(vsa):
            out = [str(vsa.get('path', ''))]
            for c in vsa.get('children', []):
                out.append(simple_tree(c))
            return out

        lec_import(dict(
            path='ut.lec_import.0',
            titles=['ut', 'lec_import', '0'],
            requires_group=None,
            lectures=[
                ['lec0', 'UT lec0'],
                ['lec1', 'UT lec1'],
            ],
            stage_template=[dict(
                name='stage%d' % i, version=0,
                title='UT stage %s' % i,
                material_tags=[],
                setting_spec={},
            ) for i in range(2)],
        ))
        lec_import(dict(
            path='ut.lec_import.1',
            titles=['ut', 'lec_import', '1'],
            requires_group=None,
            lectures=[
                ['leca', 'UT lecb'],
                ['lecb', 'UT lecb'],
            ],
            stage_template=[dict(
                name='stage%d' % i, version=0,
                title='UT stage %s' % i,
                material_tags=[],
                setting_spec={},
            ) for i in range(2)],
        ))
        self.assertEqual(
            simple_tree(view_subscription_available(self.request(user=stud))),
            ['', ['ut', ['ut.lec_import', [
                'ut.lec_import.0',
                ['ut.lec_import.0.lec0'],
                ['ut.lec_import.0.lec1'],
            ], [
                'ut.lec_import.1',
                ['ut.lec_import.1.leca'],
                ['ut.lec_import.1.lecb'],
            ]]]])

        # Remove a lecture, goes away
        lec_import(dict(
            path='ut.lec_import.0',
            titles=['ut', 'lec_import', '0'],
            requires_group=None,
            lectures=[
                ['lec0', 'UT lec0'],
                ['lec9', 'UT lec9'],
            ],
            stage_template=[dict(
                name='stage%d' % i, version=0,
                title='UT stage %s' % i,
                material_tags=[],
                setting_spec={},
            ) for i in range(2)],
        ))
        self.assertEqual(
            simple_tree(view_subscription_available(self.request(user=stud))),
            ['', ['ut', ['ut.lec_import', [
                'ut.lec_import.0',
                ['ut.lec_import.0.lec0'],
                ['ut.lec_import.0.lec9'],
            ], [
                'ut.lec_import.1',
                ['ut.lec_import.1.leca'],
                ['ut.lec_import.1.lecb'],
            ]]]])

        # clairvoyant can see dead items
        self.assertEqual(
            simple_tree(view_subscription_available(self.request(user=clairvoyant))),
            ['', ['ut', ['ut.lec_import', [
                'ut.lec_import.0',
                ['ut.lec_import.0.lec0'],
                ['ut.lec_import.0.lec1'],
                ['ut.lec_import.0.lec9'],
            ], [
                'ut.lec_import.1',
                ['ut.lec_import.1.leca'],
                ['ut.lec_import.1.lecb'],
            ]]]])
