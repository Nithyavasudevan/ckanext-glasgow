import nose

import ckan.new_tests.helpers as helpers

from ckanext.glasgow.tests import run_mock_ec
from ckanext.glasgow.tests.functional import get_test_app

eq_ = nose.tools.eq_


class TestDatasetController(object):

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

        cls.test_org = helpers.call_action('organization_create',
                                           context={'user': 'sysadmin_user'},
                                           name='test_org',
                                           extras=[{'key': 'ec_api_id',
                                                    'value': 1}])

        member = {'username': 'normal_user',
                  'role': 'admin',
                  'id': 'test_org'}
        helpers.call_action('organization_member_create',
                            context={'user': 'sysadmin_user'},
                            **member)

        # Start mock EC API
        run_mock_ec()

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_pending_dataset_page(self):

        data_dict = {
            'name': 'test_dataset_pending',
            'owner_org': 'test_org',
            'title': 'Test Dataset Pending',
            'notes': 'Some longer description',
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
        }

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('dataset_request_create',
                                           context=context,
                                           **data_dict)

        assert 'request_id' in request_dict

        response = self.app.get('/dataset/test_dataset_pending')
        eq_(response.status_int, 200)

        # Check that we got the pending page, not a default dataset page

        assert ('[Pending] {0}'.format(data_dict['title'])
                in response.html.head.title.text)

        # TODO: This is fragile, we may need to tweak once the UI is finalized
        assert request_dict['request_id'] in response.unicode_body
        assert request_dict['task_id'] in response.unicode_body

    def test_normal_dataset_page(self):

        data_dict = {
            'name': 'test_dataset',
            'owner_org': 'test_org',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
        }

        context = {'ignore_auth': True, 'local_action': True,
                   'user': self.normal_user['name']}
        dataset_dict = helpers.call_action('package_create',
                                           context=context,
                                           **data_dict)

        assert 'id' in dataset_dict

        response = self.app.get('/dataset/test_dataset')
        eq_(response.status_int, 200)

        # Check that we got the pending page, not a default dataset page

        assert (not '[Pending] {0}'.format(data_dict['title'])
                in response.html.head.title.text)
        assert (data_dict['title'] in response.html.head.title.text)
