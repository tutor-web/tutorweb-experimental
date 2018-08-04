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


Postgresql = testing.postgresql.PostgresqlFactory(
    cache_initialized_db=True,
    on_initialized=initDatabase,
)


class RequiresPostgresql():
    def setUp(self):
        super(RequiresPostgresql, self).setUp()

        self.postgresql = Postgresql()
        initDatabase(self.postgresql)

    def tearDown(self):
        self.postgresql.stop()

        super(RequiresPostgresql, self).tearDown()
