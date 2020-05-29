import os
import os.path
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
    ), check=True, stdout=subprocess.PIPE).stdout


def initDatabase(postgresql):
    dir = '../schema'
    out = []
    for s in sorted(os.listdir(dir)):
        if not s.endswith('.sql'):
            continue
        out.append(runSqlScript(postgresql, os.path.join(dir, s)))
    return b''.join(out)


Postgresql = testing.postgresql.PostgresqlFactory(
    cache_initialized_db=True,
    on_initialized=initDatabase,
)


class RequiresPostgresql():
    def setUp(self):
        super(RequiresPostgresql, self).setUp()

        # Set cwd to something known, to avoid upsetting Postgresql
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.dirname(__file__)))
        self.postgresql = Postgresql()
        os.chdir(old_cwd)
        initDatabase(self.postgresql)

    def tearDown(self):
        self.postgresql.stop()

        super(RequiresPostgresql, self).tearDown()
