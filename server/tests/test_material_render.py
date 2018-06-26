import unittest

import rpy2.robjects as robjects

from tutorweb_quizdb.material.render import rob_to_dict


class RobToDictTest(unittest.TestCase):
    def test_call(self):
        # String Vectors turn into lists
        self.assertEqual(
            rob_to_dict(robjects.r('''c('poop', 'parp')''')),
            ['poop', 'parp']
        )

        # Lists turn into dicts
        self.assertEqual(
            rob_to_dict(robjects.r('''list(poop = 12, parp = 49)''')),
            dict(poop=[12], parp=[49])
        )

        # It's recursive
        self.assertEqual(
            rob_to_dict(robjects.r('''list(poop = list(pop=list(pam="moo")), parp = 49)''')),
            dict(poop=dict(pop=dict(pam=["moo"])), parp=[49])
        )
