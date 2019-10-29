import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.student.create import create_student, generate_password


class CreateStudentTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_create_student_subscribe(self):
        def do_cs(subscribe):
            stud, password = create_student(
                self.request(),
                generate_password(10),  # NB: Not really password, a random username
                assign_password=True,
                subscribe=subscribe,
            )
            return [g.name for g in stud.groups]

        stage0 = self.create_stages(1, requires_group='ut.requires_group')
        stage1 = self.create_stages(1, requires_group='ut.requires_other_group')

        # Not subscribed to any groups by default
        self.assertEqual(do_cs([]), [])

        # Get auto-subscribed if we add to a stage that needs it.
        self.assertEqual(do_cs([
            stage0[0].syllabus.path,
            stage1[0].syllabus.path,
        ]), [
            'ut.requires_group',
            'ut.requires_other_group',
        ])
