import random

from sqlalchemy_utils import Ltree

from pyramid import testing

from tutorweb_quizdb import initialize_dbsession


class RequiresPyramid():
    def setUp(self):
        super(RequiresPyramid, self).setUp()

        self.config = testing.setUp()
        if hasattr(self, 'postgresql'):
            initialize_dbsession(dict(url=self.postgresql.url()))

    def tearDown(self):
        testing.tearDown()

        super(RequiresPyramid, self).tearDown()

    def request(self, settings={}, user=None):
        request = testing.DummyRequest()
        request.registry.settings.update(settings)
        if user:
            request.user = user
        return request

    def create_stages(self, total,
                      stage_setting_spec_fn=lambda i: {},
                      material_tags_fn=lambda i: None,
                      lec_parent='dept.tutorial'):
        from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST

        lec_name = 'lec_%d' % random.randint(1000000, 9999999)
        db_lec = Base.classes.syllabus(host_id=ACTIVE_HOST, path=Ltree(lec_parent + '.' + lec_name), title=lec_name)
        DBSession.add(db_lec)

        out = []
        for i in range(total):
            out.append(Base.classes.stage(
                syllabus=db_lec,
                stage_name='stage%d' % i, version=0,
                title='UT stage %s' % i,
                stage_setting_spec=stage_setting_spec_fn(i),
                material_tags=material_tags_fn(i),
            ))
            DBSession.add(out[-1])
        DBSession.flush()
        return out

    def create_students(self, total, student_group_fn=lambda i: ['accept_terms']):
        from tutorweb_quizdb.student.create import create_student
        from tutorweb_quizdb.student import get_group

        out = []
        for i in range(total):
            groups = [
                get_group(group_name, auto_create=True)
                for group_name
                in student_group_fn(i)
            ]

            (user, pwd) = create_student(
                self.request(),
                'user%d' % i,
                email='user%d@example.com' % i,
                assign_password=True,
                groups=groups,
            )
            out.append(user)

        return out
