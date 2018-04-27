import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.stage.setting import SettingSpec, getStudentSettings, clientside_settings


LOTS_OF_TESTS = 100000


class SettingSpecTest(unittest.TestCase):
    def test_is_customised(self):
        """Setting customised means we will choose a new value each time"""
        def is_customised(**kwargs):
            return SettingSpec(kwargs.get('key', 'x'), kwargs).is_customised()

        self.assertEqual(is_customised(value=4), False)
        self.assertEqual(is_customised(max=4), True)
        self.assertEqual(is_customised(shape=4), True)

    def test_choose_value(self):
        """Make sure we can generate all the different types of values"""
        def csv(**kwargs):
            return SettingSpec(kwargs.get('key', 'x'), kwargs).choose_value()

        # Fixed values return the value in question
        self.assertEqual(csv(value=4), '4')

        # Random values are all within bounds
        for x in range(LOTS_OF_TESTS):
            out = float(csv(max=100))
            self.assertTrue(out >= 0)
            self.assertTrue(out < 100)
        for x in range(LOTS_OF_TESTS):
            out = float(csv(min=90, max=100))
            self.assertTrue(out >= 90)
            self.assertTrue(out < 100)

        # Gamma values hit the mean
        out = 0
        for x in range(LOTS_OF_TESTS):
            out += float(csv(value=1000000, shape=2))
        out = out / LOTS_OF_TESTS
        self.assertTrue(abs(out - 2000000) < 50000)

        # String values come out unaltered, but can't be randomly chosen
        self.assertEqual(csv(key="iaa_mode", value="fun-size"), "fun-size")
        with self.assertRaisesRegexp(ValueError, 'iaa_mode'):
            csv(key="iaa_mode", value="fun-size", shape=2)
        with self.assertRaisesRegexp(ValueError, 'iaa_mode'):
            csv(key="iaa_mode", value="fun-size", max=4)

        # Integer settings get rounded, don't have "3.0" at end
        for x in range(LOTS_OF_TESTS):
            self.assertIn(csv(key="grade_nmin", max=9), '0 1 2 3 4 5 6 7 8 9'.split())

    def test_equivalent(self):
        def equiv(d1, d2):
            return SettingSpec('x', d1).equivalent(SettingSpec('x', d2))

        # After a level of precision we lose interest
        self.assertFalse(equiv(dict(max=0.01), dict(max=0.02)))
        self.assertTrue(equiv(dict(max=0.000001), dict(max=0.000002)))

        # Removing values we also notice
        self.assertFalse(equiv(dict(max=0.000001), dict(min=0.000002)))


class GetStudentSettingsTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    def replace_stage(self, db_stage, setting_spec):
        """Replace db_stage with a new version"""
        old_stage = db_stage
        db_stage = db_stage.__class__(
            hostdomain=db_stage.hostdomain,
            path=db_stage.path,
            lecture_name=db_stage.lecture_name,
            stage_name=db_stage.stage_name,
            version=db_stage.version + 1,
            title=db_stage.title,
            stage_setting_spec=setting_spec,
        )

        self.DBSession.add(db_stage)
        self.DBSession.flush()
        old_stage.next_version = db_stage.version
        self.DBSession.flush()
        return db_stage

    def test_getStudentSetting(self):
        """Student settings are stored in DB"""
        from tutorweb_quizdb import DBSession, Base
        from tutorweb_quizdb import models
        self.DBSession = DBSession

        # Add stage
        DBSession.add(Base.classes.host(hostdomain=models.ACTIVE_HOST_DOMAIN, hostkey='key'))
        DBSession.add(Base.classes.tutorial(hostdomain=models.ACTIVE_HOST_DOMAIN, path='/tut0'))
        DBSession.add(Base.classes.lecture(hostdomain=models.ACTIVE_HOST_DOMAIN, path='/tut0', lecture_name='lec0'))
        db_stage = Base.classes.stage(
            hostdomain=models.ACTIVE_HOST_DOMAIN, path='/tut0', lecture_name='lec0',
            stage_name='stage0', version=0,
            title='UT stage',
            stage_setting_spec=dict(
                hist_sel=dict(value=0.5),
                grade_s=dict(min=1, max=100),
            )
        )
        DBSession.add(db_stage)
        DBSession.flush()
        studs = [models.User(
            hostdomain=models.ACTIVE_HOST_DOMAIN,
            user_name='user%d' % i,
            email='user%d@example.com' % i,
            password='parp',
        ) for i in [0, 1, 2]]
        DBSession.add(studs[0])
        DBSession.add(studs[1])
        DBSession.add(studs[2])
        DBSession.flush()

        # Calling getStudentSettings should add student to stage as a result
        out = getStudentSettings(db_stage, studs[0])
        self.assertEqual(out, dict(
            grade_s=out['grade_s'],
            hist_sel='0.5',
        ))
        self.assertTrue(float(out['grade_s']) >= 1)
        self.assertTrue(float(out['grade_s']) < 100)
        old_grade_s = out['grade_s']

        # Can get same values again
        out = getStudentSettings(db_stage, studs[0])
        self.assertEqual(out, dict(
            grade_s=out['grade_s'],
            hist_sel='0.5',
        ))
        self.assertTrue(out['grade_s'], old_grade_s)

        # Another student gets different values
        out = getStudentSettings(db_stage, studs[1])
        self.assertEqual(out, dict(
            grade_s=out['grade_s'],
            hist_sel='0.5',
        ))
        self.assertTrue(float(out['grade_s']) >= 1)
        self.assertTrue(float(out['grade_s']) < 100)
        self.assertNotEqual(out['grade_s'], old_grade_s)

        # Replace stage with a new version
        db_stage = self.replace_stage(db_stage, dict(
            hist_sel=dict(value=0.9),
            grade_s=dict(min=1, max=100),
            grade_t=dict(min=50, max=60),
        ))

        # Students get new value for hist_sel, keep old value of grade_s
        out = getStudentSettings(db_stage, studs[0])
        self.assertEqual(out, dict(
            grade_s=out['grade_s'],
            grade_t=out['grade_t'],
            hist_sel='0.9',
        ))
        self.assertTrue(float(out['grade_t']) >= 50)
        self.assertTrue(float(out['grade_t']) < 60)
        self.assertEqual(out['grade_s'], old_grade_s)
        old_grade_t = out['grade_t']

        # Replace stage with a new version
        db_stage = self.replace_stage(db_stage, dict(
            hist_sel=dict(value=0.9),
            grade_s=dict(min=100, max=200),
            grade_t=dict(min=50, max=60),
        ))

        # This time we replace s, but keep t
        out = getStudentSettings(db_stage, studs[0])
        self.assertEqual(out, dict(
            grade_s=out['grade_s'],
            grade_t=out['grade_t'],
            hist_sel='0.9',
        ))
        self.assertTrue(float(out['grade_s']) >= 100)
        self.assertTrue(float(out['grade_s']) < 200)
        self.assertTrue(float(out['grade_t']) >= 50)
        self.assertTrue(float(out['grade_t']) < 60)
        self.assertNotEqual(out['grade_s'], old_grade_s)
        self.assertEqual(out['grade_t'], old_grade_t)
        old_grade_s = out['grade_s']

        # Replace stage with a new version
        db_stage = self.replace_stage(db_stage, dict(
            hist_sel=dict(value=0.9),
            grade_s=dict(min=100, max=200),
        ))

        # This time we keep s, but remove t
        out = getStudentSettings(db_stage, studs[0])
        self.assertEqual(out, dict(
            grade_s=out['grade_s'],
            hist_sel='0.9',
        ))
        self.assertEqual(out['grade_s'], old_grade_s)

        # Indidual empty spec treated the same as a nonexistant one
        db_stage = self.replace_stage(db_stage, dict(
            hist_sel=None,
            grade_s=dict(min=100, max=200),
        ))
        out = getStudentSettings(db_stage, studs[0])
        self.assertEqual(out, dict(
            hist_sel=None,
            grade_s=out['grade_s'],
        ))
        self.assertEqual(out['grade_s'], old_grade_s)

        # Entirely empty spec allowed
        db_stage = self.replace_stage(db_stage, None)

        # This time we got nothing
        out = getStudentSettings(db_stage, studs[0])
        self.assertEqual(out, dict(
        ))


class ClientsideSettingsTest(unittest.TestCase):
    def test_call(self):
        """Make sure we filter out known clientside-settings"""
        self.assertEqual(clientside_settings(dict(
            hist_sel='0.9',
            question_cap='55',
        )), dict(
            hist_sel='0.9',
        ))