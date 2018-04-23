import tempfile
import unittest

from tutorweb_quizdb.material.utils import file_md5sum, path_to_materialsource

from .requires_materialbank import RequiresMaterialBank


class FileMd5SumTest(unittest.TestCase):
    def test_md5sum(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b'Some file contents')
            f.flush()
            self.assertEqual(
                file_md5sum(f.name),
                '5a3de09f90eb9af33afe34bb714c28f5',
            )


class PathToMaterialSourceTest(RequiresMaterialBank, unittest.TestCase):
    def rev_parse(self, rev="HEAD"):
        return self.git('rev-parse', rev).strip()

    def test_filerevision(self):
        """Test that we parse the git file revision appropriately"""
        # File is initially untracked
        self.mb_write_file('parp', b'Some file contents')
        parp = path_to_materialsource(self.material_bank.name, 'parp', '')
        self.assertEqual(parp['revision'], '(untracked)+1')

        # ..but still versioned
        self.mb_write_file('parp', b'Some more file contents')
        parp = path_to_materialsource(self.material_bank.name, 'parp', parp['revision'])
        self.assertEqual(parp['revision'], '(untracked)+2')

        # Commit it, the dirty flag goes away
        self.mb_write_file('parp', b'Some extra file contents', commit="woo")
        parp = path_to_materialsource(self.material_bank.name, 'parp', parp['revision'])
        self.assertEqual(parp['revision'], self.git('rev-parse', 'HEAD').strip())

        # Comes back with edits
        self.mb_write_file('parp', b'Yet more file contents')
        parp = path_to_materialsource(self.material_bank.name, 'parp', parp['revision'])
        self.assertEqual(parp['revision'], self.rev_parse() + '+1')
        self.mb_write_file('parp', b'Even more file contents')
        parp = path_to_materialsource(self.material_bank.name, 'parp', parp['revision'])
        self.assertEqual(parp['revision'], self.rev_parse() + '+2')

        # Track individual files separately
        self.mb_write_file('poot', b'A different file', commit='poot')
        poot = path_to_materialsource(self.material_bank.name, 'poot', '')
        self.assertEqual(poot['revision'], self.rev_parse())
        parp = path_to_materialsource(self.material_bank.name, 'parp', parp['revision'])
        self.assertEqual(parp['revision'], self.rev_parse('HEAD^') + '+3')

    def test_fileparsing(self):
        """Test file contents are correctly parsed"""
        # Non-existant files get "deleted" tags
        example_qn = path_to_materialsource(self.material_bank.name, 'example.q.R', '')
        self.assertEqual(example_qn, dict(
            path='example.q.R',
            revision='(deleted)',
            permutationcount=0,
            materialtags=['deleted', 'type.question'],
            dataframepaths=[],
        ))

        # We combine existing tags with any derived ones
        self.mb_write_file('example.q.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:QUESTIONS=100
# TW:DATAFRAMES=agelength
        ''')
        example_qn = path_to_materialsource(self.material_bank.name, 'example.q.R', '')
        self.assertEqual(example_qn, dict(
            path='example.q.R',
            revision='(untracked)+1',
            permutationcount=100,
            materialtags=['math099', 'Q-0990t0', 'lec050500', 'type.question'],
            dataframepaths=['agelength'],
        ))

        # We also understand examples
        self.mb_write_file('example.e.R', b'''
# TW:TAGS=math099,Q-0990t0,lec050500,
# TW:QUESTIONS=2
# TW:DATAFRAMES=agelength
        ''')
        example_qn = path_to_materialsource(self.material_bank.name, 'example.e.R', '')
        self.assertEqual(example_qn, dict(
            path='example.e.R',
            revision='(untracked)+1',
            permutationcount=2,
            materialtags=['math099', 'Q-0990t0', 'lec050500', 'type.example'],
            dataframepaths=['agelength'],
        ))
