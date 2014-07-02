import nose

import ckan.new_tests.helpers as helpers

from ckanext.glasgow.tests import run_mock_ec
from ckanext.glasgow.tests.functional import get_test_app

eq_ = nose.tools.eq_


class TestChangelog(object):

    @classmethod
    def setup_class(cls):
        cls.app = get_test_app()

        # Create test user
        cls.sysadmin_user = helpers.call_action('user_create',
                                                name='sysadmin_user',
                                                email='test@test.com',
                                                password='test',
                                                sysadmin=True)

        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')
        run_mock_ec()

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_changelog_show_anon(self):

        response = self.app.get('/changelog')

        # CKAN redirects to the login page
        eq_(response.status_int, 302)

    def test_changelog_show_normal_user(self):

        extra_environ = {'REMOTE_USER': str(self.normal_user['name'])}
        response = self.app.get('/changelog', extra_environ=extra_environ,
                                status=[401])

        eq_(response.status_int, 401)

    def test_changelog_show_sysadmin_user(self):

        changelog = helpers.call_action(
            'changelog_show',
            context={'user': self.sysadmin_user['name']})

        extra_environ = {'REMOTE_USER': str(self.sysadmin_user['name'])}
        response = self.app.get('/changelog', extra_environ=extra_environ)

        eq_(response.status_int, 200)

        tables = response.html.findAll('table')

        eq_(len(tables), 1)

        cells = tables[0].findAll('tr')[1].findAll('td')

        audit = changelog[0]
        eq_(cells[0].text, str(audit['AuditId']))
        eq_(cells[1].text, audit['ObjectType'])
        eq_(cells[2].text, audit['Command'])
        eq_(cells[3].text, audit['Owner'])

    def test_changelog_show_filter_object_type(self):

        extra_environ = {'REMOTE_USER': str(self.sysadmin_user['name'])}

        for object_type in ('Dataset', 'File'):
            response = self.app.get(
                '/changelog?object_type={0}'.format(object_type),
                extra_environ=extra_environ)

            eq_(response.status_int, 200)

            tables = response.html.findAll('table')

            eq_(len(tables), 1)

            for row in tables[0].findAll('tr')[1:]:
                cell = row.findAll('td')[1]
                eq_(cell.text, object_type)
