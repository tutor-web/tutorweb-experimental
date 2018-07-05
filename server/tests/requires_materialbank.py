import os
import pathlib
import subprocess
import tempfile


class FakeMaterialSource():
    """
    Build a fake material source
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class RequiresMaterialBank():
    """
    Mixin to manage a temporary directory to treat as a material bank.
    Use self.material_name.name when you require the path
    """
    def setUp(self):
        super(RequiresMaterialBank, self).setUp()

        self.material_bank = tempfile.TemporaryDirectory()
        self.git('init')
        # Handling an empty repo is too much of an edge case, add an initial commit
        self.mb_write_file('init', b'#', commit="Initial commit")

    def tearDown(self):
        self.material_bank.cleanup()

    def git(self, *args):
        cp = subprocess.run((
            'git',
            '-C', self.material_bank.name
        ) + args, stdout=subprocess.PIPE)
        return cp.stdout.decode('utf8')

    def mb_write_file(self, file_path, content, commit=None):
        """
        Write (file_path) to the material bank, create directories as needed.
        If (commit) supplied, commit to git with the commit message
        """
        full_path = os.path.join(self.material_bank.name, file_path)
        pathlib.Path(os.path.dirname(full_path)).mkdir(parents=True, exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)
        if commit:
            self.git('add', file_path)
            self.git('commit', '-m', file_path)

    def mb_fake_ms(self, file_path):
        """Generate a fake MaterialSource object for this file"""
        from tutorweb_quizdb.material.utils import path_to_materialsource

        return FakeMaterialSource(**path_to_materialsource(
            self.material_bank.name,
            file_path,
            '0'  # Previous revision unknown
        ))

    def mb_update(self):
        """
        Update the material bank, requires RequiresPyramid to be mixed in too
        """
        from tutorweb_quizdb.material.update import view_material_update

        if not hasattr(self, 'request'):
            raise ValueError("request not defined, RequiresPyramid probably missing")

        request = self.request(settings={'tutorweb.material_bank.default': self.material_bank.name})
        return view_material_update(request)
