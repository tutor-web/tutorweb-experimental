import unittest

from pyramid_mailer import get_mailer

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.student.create import activate_trigger_email, create_student, generate_password
from tutorweb_quizdb.auth.activate import includeme


class ActivateTriggerEmailTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    def test_call(self):
        def ate(user):
            request = self.request()
            mailer = get_mailer(request)
            old_len = len(mailer.outbox)
            activate_trigger_email(request, user)
            return mailer.outbox[old_len] if len(mailer.outbox) > old_len else None

        self.config.include('pyramid_mailer.testing')
        includeme(self.config)  # NB: We need the activate routes available
        db_studs = self.create_students(2)

        # Do nothing if it wasn't a valid user
        self.assertEqual(ate("notauser@example.com"), None)

        # Can trigger via. user object...
        out = ate(db_studs[0])
        self.assertIn(db_studs[0].email, out.send_to)
        self.assertIn(db_studs[0].username, out.body)

        # Via username...
        out = ate(db_studs[1].username)
        self.assertIn(db_studs[1].email, out.send_to)
        self.assertIn(db_studs[1].username, out.body)

        # Via email...
        out = ate(db_studs[1].email)
        self.assertIn(db_studs[1].email, out.send_to)
        self.assertIn(db_studs[1].username, out.body)


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
