from pyramid import testing

from tutorweb_quizdb import initialize_dbsession


class RequiresPyramid():
    def setUp(self):
        super(RequiresPyramid, self).setUp()

        self.config = testing.setUp()
        if hasattr(self, 'postgresql'):
            initialize_dbsession(self.postgresql.url())

    def tearDown(self):
        testing.tearDown()

        super(RequiresPyramid, self).tearDown()

    def request(self, settings={}):
        request = testing.DummyRequest()
        request.registry.settings.update(settings)
        return request
