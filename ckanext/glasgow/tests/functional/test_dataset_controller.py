import nose
import mock
import json

from bs4 import BeautifulSoup

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

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    def test_pending_dataset_page(self, mock_token):
        mock_token.return_value = 'Bearer: token'

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

        response = self.app.get('/dataset/test_dataset_pending',
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        eq_(response.status_int, 200)

        # Check that we got the pending page, not a default dataset page

        assert ('[Pending] {0}'.format(data_dict['title'])
                in response.html.head.title.text)

        # Check for EC API status in response
        assert 'State - Succeeded' in response.body
        assert 'File Create Operation completed' in response.body

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

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    def test_pending_file_on_dataset_page(self, mock_token):
        mock_token.return_value = 'Bearer: token'

        data_dict = {
            'name': 'test_dataset_file_pending',
            'owner_org': 'test_org',
            'title': 'Test Dataset Pending File',
            'notes': 'Some longer description',
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
            'ec_api_id': "1",
        }

        context = {'ignore_auth': True, 'local_action': True,
                   'user': self.normal_user['name']}
        dataset_dict = helpers.call_action('package_create',
                                           context=context,
                                           **data_dict)

        assert 'id' in dataset_dict

        data_dict = {
            'dataset_id': dataset_dict['id'],
            'name': 'test_file',
            'description': 'test description',
            'format': 'no format',
            'url': 'http://test.com',
        }

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('file_request_create',
                                           context=context,
                                           **data_dict)

        response = self.app.get('/dataset/test_dataset_file_pending',
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        eq_(response.status_int, 200)

        pending = response.html.find('li', {'id': 'pending-1'})
        assert 'test_file' in pending.a.text
        assert 'test description' in pending.p.text


    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_pending_dataset_update(self, mock_request, mock_token):
        def request_result(*args, **kwargs):
            if 'ChangeLog' in args[1]:
                return mock.Mock(
                    status_code=200,
                    content=json.dumps({'RequestId': 'req-id'}),
                    **{
                        'raise_for_status.return_value': None,
                        'json.return_value': [{
                            'operation_state': 'InProgress',
                            'audit_id': 998,
                            'timestamp': '2014-05-21T00:00:00',
                            'object_type': 'Dataset',
                            'component': 'DataCollection',
                            'audit_type': 'DatasetUpdateRequested',
                            'owner': 'Admin', 
                            'message': 'Dataset Update request started',
                            'command': 'CreateFile'
                            }]
                    }
                )
            else:
                return mock.Mock(
                    status_code=200,
                    content=json.dumps({'RequestId': 'req-id'}),
                    **{
                        'raise_for_status.return_value': None,
                        'json.return_value': {'RequestId': 'req-id'},
                    }
                )


        mock_token.return_value = 'Bearer: token'
        # make the mock the result of calling requests.request(...)
        mock_request.side_effect =  request_result

        context = {'local_action': True, 'user': 'normal_user'}
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

        self.dataset = helpers.call_action('package_create', context=context,
                                          **data_dict)

        data_dict = self.dataset.copy()
        data_dict.update({
            'notes': 'Updated longer description',
            'tags': [
                {'name': 'Test tag 1'},
                {'name': 'Test tag 2'},
            ],
            'published_on_behalf_of': 'Test published on behalf of',
            'usage_guidance': 'Test usage guidance',
            'category': 'Test category',
            'theme': 'Test theme',
            'standard_name': 'Test standard name',
            'standard_rating': 5,
            'standard_version': 'Test standard version',
        })

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('dataset_request_update',
                                           context=context,
                                           **data_dict)

        response = self.app.get('/dataset/change_requests/test_dataset',
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        soup = BeautifulSoup(response.body)
        nose.tools.assert_true('State - InProgress' in soup.table.text)
        nose.tools.assert_true('Timestamp - 2014-05-21T00:00:00' in soup.table.text)
        nose.tools.assert_true('Type - Dataset' in soup.table.text)
        nose.tools.assert_true('Message - Dataset Update request started' in soup.table.text)
