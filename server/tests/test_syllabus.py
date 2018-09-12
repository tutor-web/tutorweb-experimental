import unittest

from sqlalchemy_utils import Ltree

from tutorweb_quizdb.syllabus import path_to_ltree


class PathToLtreeTest(unittest.TestCase):
    def test_call(self):
        self.assertEqual(
            path_to_ltree('comp.crypto'),
            Ltree('comp.crypto'))

        # Munge a URI for the half-ported client code
        self.assertEqual(
            path_to_ltree('/api/stage?path=class.haskoli_islands.612.0.lecture120.stage1'),
            Ltree('class.haskoli_islands.612.0.lecture120.stage1'))

        # nearest-tut finds the closest tutorial-like thing
        self.assertEqual(
            path_to_ltree('nearest-tut:class.haskoli_islands.612.0.lecture120.stage1'),
            Ltree('class.haskoli_islands.612.0'))
        self.assertEqual(
            path_to_ltree('nearest-tut:comp.crypto251.0.lec00100.stage0'),
            Ltree('comp.crypto251.0'))
        self.assertEqual(
            path_to_ltree('nearest-tut:comp.crypto251.0'),
            Ltree('comp.crypto251.0'))

        # Go outside a tutorial-level, just pass through
        self.assertEqual(
            path_to_ltree('nearest-tut:comp'),
            Ltree('comp'))

        # Can combine URI-dereference and nearest-tut
        self.assertEqual(
            path_to_ltree('nearest-tut:/api/stage?path=class.haskoli_islands.612.0.lecture120.stage1'),
            Ltree('class.haskoli_islands.612.0'))
        self.assertEqual(
            path_to_ltree('/api/stage?path=nearest-tut:class.haskoli_islands.612.0.lecture120.stage1'),
            Ltree('class.haskoli_islands.612.0'))
