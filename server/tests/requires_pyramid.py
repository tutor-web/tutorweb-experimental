from pyramid import testing

from tutorweb_quizdb import initialize_dbsession


class RequiresPyramid():
    def setUp(self):
        super(RequiresPyramid, self).setUp()

        self.config = testing.setUp()
        if self.postgresql:
            initialize_dbsession({
                'sqlalchemy.url': self.postgresql.url(),
                'sqlalchemy.echo': False,  # Set to true to log SQL statements
            })

    def tearDown(self):
        testing.tearDown()

        super(RequiresPyramid, self).tearDown()

    def request(self, settings={}):
        request = testing.DummyRequest()
        request.registry.settings.update(settings)
        return request
