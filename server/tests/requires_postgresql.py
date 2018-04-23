import os
import subprocess

import testing.postgresql


def runSqlScript(postgresql, script):
    return subprocess.run((
        'psql', '-b',
        '-f', script,
        '-h', 'localhost',
        '-p', str(postgresql.settings['port']),
        '-U', 'postgres', '-w',
        'test',
    ), check=True, stdout=subprocess.PIPE)


def initDatabase(postgresql):
    dir = '../schema'
    for s in sorted(os.listdir(dir)):
        if not s.endswith('.sql'):
            continue
        runSqlScript(postgresql, os.path.join(dir, s))


Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


class RequiresPostgresql():
    def setUp(self):
        super(RequiresPostgresql, self).setUp()

        self.postgresql = testing.postgresql.Postgresql()
        initDatabase(self.postgresql)  # TODO: In theory we can use on_initialized, but the results get rolled back somewhere?

    def tearDown(self):
        self.postgresql.stop()

        super(RequiresPostgresql, self).tearDown()
