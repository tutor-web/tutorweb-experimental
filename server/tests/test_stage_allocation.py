import unittest

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid
from .requires_materialbank import RequiresMaterialBank

from tutorweb_quizdb.stage.allocation import get_allocation


class OriginalAllocationTest(unittest.TestCase):
    def test_to_from_public_id(self):
        """to/from public_id should be able to recover information"""
        alloc_a = get_allocation(dict(
            allocation_method='original',
            allocation_seed=44,
            allocation_encryption_key='toottoottoot',
        ), 'fake_db_stage', 'fake_db_student')

        self.assertEqual((11, 34), alloc_a.from_public_id(alloc_a.to_public_id(11, 34)))
        self.assertEqual((33, 31), alloc_a.from_public_id(alloc_a.to_public_id(33, 31)))
        self.assertNotEqual(
            alloc_a.to_public_id(11, 34),
            alloc_a.to_public_id(33, 31),
        )

        alloc_b = get_allocation(dict(
            allocation_method='original',
            allocation_seed=44,
            allocation_encryption_key='parpparpparp',
        ), 'fake_db_stage', 'fake_db_student')

        self.assertEqual((11, 34), alloc_b.from_public_id(alloc_b.to_public_id(11, 34)))
        self.assertEqual((33, 31), alloc_b.from_public_id(alloc_b.to_public_id(33, 31)))
        self.assertNotEqual(
            alloc_b.to_public_id(11, 34),
            alloc_b.to_public_id(33, 31),
        )

        # The 2 allocations don't generate the same public IDs
        self.assertNotEqual(
            alloc_a.to_public_id(11, 34),
            alloc_b.to_public_id(11, 34),
        )

    def test_should_refresh_questions(self):
        """Refresh based on refresh_interval"""
        alloc_a = get_allocation(dict(
            allocation_method='original',
            allocation_seed=44,
            allocation_encryption_key='toottoottoot',
            allocation_refresh_interval=10,
        ), 'fake_db_stage', 'fake_db_student')

        self.assertFalse(alloc_a.should_refresh_questions([], 0))
        self.assertFalse(alloc_a.should_refresh_questions([dict()] * 5, 1))
        # NB: additions are already included in the answer queue by this point
        self.assertTrue(alloc_a.should_refresh_questions([dict()] * 10, 5))
        self.assertTrue(alloc_a.should_refresh_questions([dict()] * 11, 2))
        self.assertTrue(alloc_a.should_refresh_questions([dict()] * 22, 5))


class OriginalAllocationDBTest(RequiresPyramid, RequiresMaterialBank, RequiresPostgresql, unittest.TestCase):
    def test_get_material(self):
        self.mb_write_example('common1_question.q.R', ('all', 'common1',), 3)
        self.mb_write_example('common2_question.q.R', ('all', 'common2',), 3)
        self.mb_update()

        self.db_stages = self.create_stages(3, lambda i: dict(
        ), lambda i: [
            'type.question',
            'all' if i == 0 else 'common%d' % (i // 2 + 1),
        ])
        self.db_studs = self.create_students(3)

        alloc_a = get_allocation(dict(
            allocation_method='original',
            allocation_seed=44,
            allocation_encryption_key='toottoottoot',
        ), self.db_stages[0], self.db_studs[0])
        out = [(self.mb_lookup_mss_id(x[0]).path, x[1], x[2], x[3]) for x in alloc_a.get_material()]
        self.assertEqual(set(out), set([
            ('common1_question.q.R', 1, 0, 0),
            ('common1_question.q.R', 2, 0, 0),
            ('common1_question.q.R', 3, 0, 0),
            ('common2_question.q.R', 1, 0, 0),
            ('common2_question.q.R', 2, 0, 0),
            ('common2_question.q.R', 3, 0, 0),
        ]))

        alloc_a = get_allocation(dict(
            allocation_method='original',
            allocation_seed=44,
            allocation_encryption_key='toottoottoot',
        ), self.db_stages[1], self.db_studs[0])
        out = [(self.mb_lookup_mss_id(x[0]).path, x[1], x[2], x[3]) for x in alloc_a.get_material()]
        self.assertEqual(set(out), set([
            ('common1_question.q.R', 1, 0, 0),
            ('common1_question.q.R', 2, 0, 0),
            ('common1_question.q.R', 3, 0, 0),
        ]))

        alloc_a = get_allocation(dict(
            allocation_method='original',
            allocation_seed=44,
            allocation_encryption_key='toottoottoot',
        ), self.db_stages[2], self.db_studs[0])
        out = [(self.mb_lookup_mss_id(x[0]).path, x[1], x[2], x[3]) for x in alloc_a.get_material()]
        self.assertEqual(set(out), set([
            ('common2_question.q.R', 1, 0, 0),
            ('common2_question.q.R', 2, 0, 0),
            ('common2_question.q.R', 3, 0, 0),
        ]))

        # TODO: Test capping / sampling
