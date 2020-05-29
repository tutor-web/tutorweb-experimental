import unittest

from pyramid.httpexceptions import HTTPForbidden

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.student import get_group
from tutorweb_quizdb.syllabus.bulk_subscribe import view_bulk_subscribe


class BulkSubscribeTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_bulk_subscribe(self):
        teacher = self.create_students(1)[0]
        stages = self.create_stages(1, requires_group='class.bulk_subscribe')

        def vbs(users):
            return view_bulk_subscribe(self.request(
                user=teacher,
                params=dict(path=str(stages[0].syllabus.path)),
                body=dict(users=users, assign_password=True),
            ))

        # The view version requires admin permissions
        with self.assertRaisesRegex(HTTPForbidden, 'admin'):
            vbs(['cuthbert@example.com'])
        teacher.groups.append(get_group('admin.%s' % stages[0].syllabus.path, auto_create=True))

        # Add some pupils
        out = vbs(['cuthbert@example.com', 'dibble@example.com'])
        self.assertEqual(out, dict(users=[
            dict(user_name='cuthbert@example.com', email='cuthbert@example.com', password=out['users'][0]['password']),
            dict(user_name='dibble@example.com', email='dibble@example.com', password=out['users'][1]['password']),
        ]))
        self.assertEqual([ug.user.user_name for ug in get_group('class.bulk_subscribe').usergroup_collection], [
            'cuthbert@example.com',
            'dibble@example.com',
        ])

        # Add some more, old ones don't get recreated, don't get a new password
        out = vbs(['cuthbert@example.com', 'dibble@example.com', 'grub@example.com'])
        self.assertEqual(out, dict(users=[
            dict(user_name='cuthbert@example.com', email='cuthbert@example.com', password=''),
            dict(user_name='dibble@example.com', email='dibble@example.com', password=''),
            dict(user_name='grub@example.com', email='grub@example.com', password=out['users'][2]['password']),
        ]))
        self.assertEqual([u.user_name for u in get_group('class.bulk_subscribe').users], [
            'cuthbert@example.com',
            'dibble@example.com',
            'grub@example.com',
        ])
