import unittest
import unittest.mock

from tutorweb_quizdb.syllabus.add import multiple_lec_import


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
