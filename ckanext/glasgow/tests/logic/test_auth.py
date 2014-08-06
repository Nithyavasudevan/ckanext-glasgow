import json
import mock
import nose

import ckan.plugins as p
import ckan.new_tests.helpers as helpers

eq_ = nose.tools.eq_


class TestCreate(object):

    @classmethod
    def setup_class(cls):

        # Create test users and other objects

        cls.sysadmin_user = helpers.call_action('user_create',
                                                name='sysadmin_user',
                                                email='test@test.com',
                                                password='test',
                                                sysadmin=True)

        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'sysadmin_user',
                                           'local_action': True,
                                        },
                                       name='test_org')

        member = {'username': 'normal_user',
                  'role': 'admin',
                  'id': 'test_org'}
        helpers.call_action('organization_member_create',
                            context={'user': 'sysadmin_user'},
                            **member)

        cls.normal_user_no_org = helpers.call_action('user_create',
                                                     name='normal_user_no_org',
                                                     email='test@test.com',
                                                     password='test')

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_package_create_anon(self):

        context = {}

        data_dict = {
            'name': 'test_dataset_name',
        }

        nose.tools.assert_raises(p.toolkit.NotAuthorized,
                                 p.toolkit.check_access,
                                 'package_create', context, data_dict)

    def test_package_create_normal_user(self):

        context = {}
        context['user'] = 'normal_user'

        data_dict = {
            'name': 'test_dataset_name',
        }

        p.toolkit.check_access('package_create', context, data_dict)

    def test_package_create_sysadmin(self):

        context = {}
        context['user'] = 'sysadmin_user'
        context['local_action'] = True

        data_dict = {
            'name': 'test_dataset_name',
        }
        p.toolkit.check_access('package_create', context, data_dict)

    def test_package_create_local_normal_user(self):

        context = {}
        context['user'] = 'normal_user'
        context['local_action'] = True

        data_dict = {
            'name': 'test_dataset_name',
        }

        nose.tools.assert_raises(p.toolkit.NotAuthorized,
                                 p.toolkit.check_access,
                                 'package_create', context, data_dict)

    def test_package_create_local_sysadmin(self):

        context = {}
        context['user'] = 'sysadmin_user'
        context['local_action'] = True

        data_dict = {
            'name': 'test_dataset_name',
        }
        p.toolkit.check_access('package_create', context, data_dict)

    def test_dataset_request_create_anon(self):

        context = {}

        data_dict = {
            'name': 'test_dataset_name',
        }

        nose.tools.assert_raises(p.toolkit.NotAuthorized,
                                 p.toolkit.check_access,
                                 'package_create', context, data_dict)
# TODO: Clarify these settings
#    def test_dataset_request_create_normal_user_no_org(self):
#
#        context = {}
#        context['user'] = 'normal_user_no_org'
#
#        data_dict = {
#            'name': 'test_dataset_name',
#        }
#
#        nose.tools.assert_raises(p.toolkit.NotAuthorized,
#                                 p.toolkit.check_access,
#                                 'package_create', context, data_dict)

    def test_dataset_request_create_normal_user(self):

        context = {}
        context['user'] = 'normal_user'

        data_dict = {
            'name': 'test_dataset_name',
        }

        p.toolkit.check_access('package_create', context, data_dict)

    def test_dataset_request_create_sysadmin(self):

        context = {}
        context['user'] = 'sysadmin_user'

        data_dict = {
            'name': 'test_dataset_name',
        }

        p.toolkit.check_access('package_create', context, data_dict)


class TestChangelog(object):

    @classmethod
    def setup_class(cls):

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

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_changelog_show_anon(self):

        context = {}
        data_dict = {}

        nose.tools.assert_raises(p.toolkit.NotAuthorized,
                                 p.toolkit.check_access,
                                 'changelog_show', context, data_dict)

    def test_changelog_show_normal_user(self):

        context = {}
        context['user'] = 'normal_user'
        data_dict = {}

        nose.tools.assert_raises(p.toolkit.NotAuthorized,
                                 p.toolkit.check_access,
                                 'changelog_show', context, data_dict)

    def test_changelog_show_sysadmin(self):

        context = {}
        context['user'] = 'sysadmin_user'
        data_dict = {}

        p.toolkit.check_access('changelog_show', context, data_dict)


class TestOrganizations(object):
    def setup(self):
        self.sysadmin_user = helpers.call_action('user_create',
                                                name='sysadmin_user',
                                                email='test@test.com',
                                                password='test',
                                                sysadmin=True)

        self.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'sysadmin_user',
                                           'local_action': True,
                                       },
                                       name='test_org')

    def teardown(self):
        helpers.reset_db()

    def test_non_owner_cannot_add_members(self):
        context = {'user': self.normal_user['name'], 'ignore_auth': False}
        nose.tools.assert_raises(p.toolkit.NotAuthorized,
            helpers.call_action,
            'organization_member_create',
            context=context,
            id=self.test_org['id'],
            username=self.normal_user['name'],
            role='member',
        )
