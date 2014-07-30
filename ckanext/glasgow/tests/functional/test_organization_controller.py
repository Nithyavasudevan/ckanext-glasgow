import json
import mock

from bs4 import BeautifulSoup
import nose.tools

import ckan.new_tests.helpers as helpers

from ckanext.glasgow.tests.functional import get_test_app


class TestOrganizationController(object):
    def setup(self):
        self.app = get_test_app()

        # Create test user
        self.sysadmin_user = helpers.call_action('user_create',
                                                name='sysadmin_user',
                                                email='test@test.com',
                                                password='test',
                                                sysadmin=True)

        self.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

    def teardown(self):
        helpers.reset_db()

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_pending_organization_page(self, mock_request, mock_token):
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
                            'object_type': 'Organisation',
                            'component': 'DataCollection',
                            'audit_type': 'OrganisationCreateRequested',
                            'owner': 'Admin', 
                            'message': 'Organisation Create request started',
                            'command': 'CreateOrganisation'
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

        request_dict = helpers.call_action(
            'organization_request_create',
            context={'user' : self.normal_user['name']},
            name='test_pending_org',
            needs_approval=False
        )

        response = self.app.get('/organization/test_pending_org',
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        nose.tools.assert_equals(response.status_int, 200)
        nose.tools.assert_in(request_dict['name'], response.html.head.title.text)


    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_normal_organization_page(self, mock_request, mock_token):
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
                            'object_type': 'Organisation',
                            'component': 'DataCollection',
                            'audit_type': 'OrganisationCreateRequested',
                            'owner': 'Admin', 
                            'message': 'Organisation Create request started',
                            'command': 'CreateOrganisation'
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

        context = {'ignore_auth': True, 'local_action': True,
                   'user': self.normal_user['name']}
        request_dict = helpers.call_action(
            'organization_create',
            context=context,
            name='test_not_pending_org',
            needs_approval=False
        )

        response = self.app.get('/organization/test_not_pending_org',
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        nose.tools.assert_equals(response.status_int, 200)
        nose.tools.assert_not_in('Pending', response.html.head.title.text)


class TestOrganizationUpdateController(object):
    def setup(self):
        self.app = get_test_app()

        # Create test user
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
                                           'user': 'normal_user',
                                           'local_action': True,
                                       },
                                       name='test_org')

    def teardown(self):
        helpers.reset_db()

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_pending_organization_update(self, mock_request, mock_token):
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
                            'object_type': 'Organization',
                            'component': 'DataCollection',
                            'audit_type': 'OrganizationUpdateRequested',
                            'owner': 'Admin', 
                            'message': 'Organization Update request started',
                            'command': 'OrganizationUpdate'
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


        data_dict = self.test_org.copy()
        data_dict.update({
            'needs_approval': False,
            'description': 'updated description',
        })

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('organization_request_update',
                                           context=context,
                                           **data_dict)

        response = self.app.get('/organization/change_requests/{0}'.format(self.test_org['id']),
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        soup = BeautifulSoup(response.body)
        nose.tools.assert_true('State - InProgress' in soup.table.text)
        nose.tools.assert_true('Timestamp - 2014-05-21T00:00:00' in soup.table.text)
        nose.tools.assert_true('Type - Organization' in soup.table.text)
        nose.tools.assert_true('Message - Organization Update request started' in soup.table.text)

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_pending_organization_name_update(self, mock_request, mock_token):
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
                            'object_type': 'Organization',
                            'component': 'DataCollection',
                            'audit_type': 'OrganizationUpdateRequested',
                            'owner': 'Admin', 
                            'message': 'Organization Update request started',
                            'command': 'OrganizationUpdate'
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


        data_dict = self.test_org.copy()
        data_dict.update({
            'name': 'updated_name',
            'needs_approval': False,
            'description': 'updated description',
        })

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('organization_request_update',
                                           context=context,
                                           **data_dict)

        response = self.app.get('/organization/change_requests/{0}'.format(self.test_org['id']),
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        soup = BeautifulSoup(response.body)
        nose.tools.assert_true('State - InProgress' in soup.table.text)
        nose.tools.assert_true('Timestamp - 2014-05-21T00:00:00' in soup.table.text)
        nose.tools.assert_true('Type - Organization' in soup.table.text)
        nose.tools.assert_true('Message - Organization Update request started' in soup.table.text)

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_pending_organization_by_name_in_url(self, mock_request, mock_token):
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
                            'object_type': 'Organization',
                            'component': 'DataCollection',
                            'audit_type': 'OrganizationUpdateRequested',
                            'owner': 'Admin', 
                            'message': 'Organization Update request started',
                            'command': 'OrganizationUpdate'
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


        data_dict = self.test_org.copy()
        data_dict.update({
            'name': 'updated_name',
            'needs_approval': False,
            'description': 'updated description',
        })

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('organization_request_update',
                                           context=context,
                                           **data_dict)

        response = self.app.get('/organization/change_requests/test_org',
                                extra_environ={'REMOTE_USER': 'sysadmin_user'})
        soup = BeautifulSoup(response.body)
        nose.tools.assert_true('State - InProgress' in soup.table.text)
        nose.tools.assert_true('Timestamp - 2014-05-21T00:00:00' in soup.table.text)
        nose.tools.assert_true('Type - Organization' in soup.table.text)
        nose.tools.assert_true('Message - Organization Update request started' in soup.table.text)
