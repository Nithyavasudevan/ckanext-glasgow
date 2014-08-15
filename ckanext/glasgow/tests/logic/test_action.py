import cgi
import datetime
import os
import StringIO
import json

import nose
import mock

from pylons import config
import requests

import ckan.model as model
import ckan.plugins as p
import ckan.new_tests.helpers as helpers
from ckan.lib import search


from ckanext.glasgow.logic.action import (
    _get_api_endpoint,
    _create_task_status,
    _update_task_status_success,
    _update_task_status_error,
    ECAPINotAuthorized,
    ECAPIError,
    )

from ckanext.glasgow.tests import run_mock_ec


eq_ = nose.tools.eq_


class TestGetAPIEndpoint(object):

    @classmethod
    def setup_class(cls):

        cls._base_data_collection_api = 'https://base.data_collection.api/'
        cls._base_metadata_api = 'https://base.metadata.api/'
        cls._base_identity_api = 'https://base.identity.api/'

        config['ckanext.glasgow.data_collection_api'] = cls._base_data_collection_api
        config['ckanext.glasgow.metadata_api'] = cls._base_metadata_api
        config['ckanext.glasgow.identity_api'] = cls._base_identity_api

    def test_get_api_endpoint(self):
        write_base_api = self._base_data_collection_api.rstrip('/')
        read_base_api = self._base_metadata_api.rstrip('/')
        identity_base_api = self._base_identity_api.rstrip('/')

        eq_(_get_api_endpoint('dataset_show'),
            ('GET', read_base_api + '/Metadata/Organisation/{organization_id}/Dataset/{dataset_id}'))
        eq_(_get_api_endpoint('dataset_request_create'),
            ('POST', write_base_api + '/Datasets/Organisation/{organization_id}'))
        eq_(_get_api_endpoint('dataset_request_update'),
            ('PUT', write_base_api + '/Datasets/Organisation/{organization_id}/Dataset/{dataset_id}'))

        eq_(_get_api_endpoint('file_show'),
            ('GET', read_base_api + '/Metadata/Organisation/{organization_id}/Dataset/{dataset_id}/File/{file_id}'))
        eq_(_get_api_endpoint('file_request_create'),
            ('POST', write_base_api + '/Files/Organisation/{organization_id}/Dataset/{dataset_id}'))
        eq_(_get_api_endpoint('file_request_update'),
            ('PUT', write_base_api + '/Files/Organisation/{organization_id}/Dataset/{dataset_id}'))
        eq_(_get_api_endpoint('file_versions_show'),
            ('GET', read_base_api + '/Metadata/Organisation/{organization_id}/Dataset/{dataset_id}/File/{file_id}/Versions'))
        eq_(_get_api_endpoint('file_version_show'),
            ('GET', read_base_api + '/Metadata/Organisation/{organization_id}/Dataset/{dataset_id}/File/{file_id}/Versions/{version_id}'))

        eq_(_get_api_endpoint('organization_show'),
            ('GET', read_base_api + '/Metadata/Organisation/{organization_id}'))
        eq_(_get_api_endpoint('organization_request_create'),
            ('POST', write_base_api + '/Organisations'))
        eq_(_get_api_endpoint('organization_request_update'),
            ('PUT', write_base_api + '/Organisations/Organisation/{organization_id}'))

        eq_(_get_api_endpoint('request_status_show'),
            ('GET', read_base_api + '/ChangeLog/RequestStatus/{request_id}'))
        eq_(_get_api_endpoint('changelog_show'),
            ('GET', read_base_api + '/ChangeLog/RequestChanges'))

        eq_(_get_api_endpoint('user_role_update'),
            ('PUT', identity_base_api + '/UserRoles/Organisation/{organization_id}/User/{user_id}'))


class TestTaskStatusHelpers(object):

    def setup(cls):
        helpers.reset_db()

    def test_create_task_status(self):

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_entity_id',
                                        entity_type='test_entity_type',
                                        key='test_key',
                                        value='test_value'
                                        )

        assert 'id' in task_dict
        eq_(task_dict['task_type'], 'test_task_type')
        eq_(task_dict['entity_id'], 'test_entity_id')
        eq_(task_dict['entity_type'], 'test_entity_type')
        eq_(task_dict['key'], 'test_key')
        eq_(task_dict['value'], 'test_value')
        eq_(task_dict['state'], 'new')

        task = model.Session.query(model.TaskStatus) \
                            .filter(model.TaskStatus.id == task_dict['id']) \
                            .one()

        # Check the DB was actually updated
        eq_(task.task_type, 'test_task_type')
        eq_(task.entity_id, 'test_entity_id')
        eq_(task.entity_type, 'test_entity_type')
        eq_(task.key, 'test_key')
        eq_(task.value, 'test_value')
        eq_(task.state, 'new')

    def test_update_task_status_success(self):

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_entity_id',
                                        entity_type='test_entity_type',
                                        key='test_key',
                                        value='test_value'
                                        )

        task_dict = _update_task_status_success({'user': 'test'},
                                                task_dict=task_dict,
                                                value='test_value_updated'
                                                )

        assert 'id' in task_dict
        eq_(task_dict['task_type'], 'test_task_type')
        eq_(task_dict['entity_id'], 'test_entity_id')
        eq_(task_dict['entity_type'], 'test_entity_type')
        eq_(task_dict['key'], 'test_key')
        eq_(task_dict['value'], 'test_value_updated')
        eq_(task_dict['state'], 'sent')

        task = model.Session.query(model.TaskStatus) \
                            .filter(model.TaskStatus.id == task_dict['id']) \
                            .one()

        # Check the DB was actually updated
        eq_(task.value, 'test_value_updated')
        eq_(task.state, 'sent')

    def test_update_task_status_error(self):

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_entity_id',
                                        entity_type='test_entity_type',
                                        key='test_key',
                                        value='test_value'
                                        )

        task_dict = _update_task_status_error({'user': 'test'},
                                              task_dict=task_dict,
                                              value='test_value_updated'
                                              )

        assert 'id' in task_dict
        eq_(task_dict['task_type'], 'test_task_type')
        eq_(task_dict['entity_id'], 'test_entity_id')
        eq_(task_dict['entity_type'], 'test_entity_type')
        eq_(task_dict['key'], 'test_key')
        eq_(task_dict['value'], 'test_value_updated')
        eq_(task_dict['state'], 'error')

        task = model.Session.query(model.TaskStatus) \
                            .filter(model.TaskStatus.id == task_dict['id']) \
                            .one()

        # Check the DB was actually updated
        eq_(task.value, 'test_value_updated')
        eq_(task.state, 'error')


class TestTaskStatus(object):

    @classmethod
    def setup_class(cls):
        helpers.reset_db()

    def test_pending_task_for_dataset_by_name(self):

        context = {'user': 'test'}
        task_dict = _create_task_status(context,
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           context=context,
                                           name='test_dataset_name'
                                           )

        eq_(pending_task['id'], task_dict['id'])
        eq_(pending_task['state'], 'new')

    def test_pending_task_for_dataset_by_id(self):

        context = {'user': 'test'}
        task_dict = _create_task_status(context,
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           context=context,
                                           id='test_dataset_id'
                                           )

        eq_(pending_task['id'], task_dict['id'])
        eq_(pending_task['state'], 'new')

    def test_pending_task_for_dataset_success_found(self):

        context = {'user': 'test'}
        task_dict = _create_task_status(context,
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        task_dict = _update_task_status_success(context,
                                                task_dict=task_dict,
                                                value='test_value_updated'
                                                )

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           context=context,
                                           id='test_dataset_id'
                                           )

        eq_(pending_task['id'], task_dict['id'])
        eq_(pending_task['state'], 'sent')

    def test_pending_task_for_dataset_error_not_found(self):

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        task_dict = _update_task_status_error({'user': 'test'},
                                              task_dict=task_dict,
                                              value='test_value_updated'
                                              )

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           id='test_dataset_id'
                                           )

        eq_(pending_task, None)

    def test_pending_task_for_dataset_not_found(self):

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           id='unexisting_dataset'
                                           )

        eq_(pending_task, None)


class TestDatasetCreate(object):

    @classmethod
    def setup_class(cls):

        # Create test user
        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        # Create test org
        test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'normal_user',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       extras=[{'key': 'ec_api_id',
                                                'value': 1}])

        # Start mock EC API
        run_mock_ec()

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_create(self):

        data_dict = {
            'name': 'test_dataset',
            'owner_org': 'test_org',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'needs_approval': False,
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'tags': [
                {'name': 'Test tag 1'},
                {'name': 'Test tag 2'},
            ],
            'openness_rating': 3,
            'quality': 5,
            'published_on_behalf_of': 'Test published on behalf of',
            'usage_guidance': 'Test usage guidance',
            'category': 'Test category',
            'theme': 'Test theme',
            'standard_name': 'Test standard name',
            'standard_rating': 5,
            'standard_version': 'Test standard version',
        }

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('dataset_request_create',
                                           context=context,
                                           **data_dict)

        assert 'task_id' in request_dict
        eq_(len(request_dict['task_id']), 36)

        assert 'request_id' in request_dict
        # TODO: test format when known
        assert request_dict['request_id']

        # Check that TaskStatus was actually created
        task_dict = helpers.call_action('task_status_show',
                                        id=request_dict['task_id'])

        eq_(task_dict['id'], request_dict['task_id'])
        eq_(task_dict['task_type'], 'dataset_request_create')
        eq_(task_dict['entity_type'], 'dataset')
        eq_(task_dict['key'], data_dict['name'])
        eq_(task_dict['state'], 'sent')
        assert 'data_dict' in json.loads(task_dict['value'])

    def test_create_ec_401(self):

        data_dict = {
            'name': 'test_dataset-401',
            'owner_org': 'test_org',
            'title': 'Test Dataset 401',
            'notes': 'Some longer description',
            'needs_approval': False,
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'tags': [
                {'name': 'Test tag 1'},
                {'name': 'Test tag 2'},
            ],
            'openness_rating': 3,
            'quality': 5,
            'published_on_behalf_of': 'Test published on behalf of',
            'usage_guidance': 'Test usage guidance',
            'category': 'Test category',
            'theme': 'Test theme',
            'standard_name': 'Test standard name',
            'standard_rating': 5,
            'standard_version': 'Test standard version',
        }

        # This will make the mock EC API return a 401
        os.environ['__CKANEXT_GLASGOW_AUTH_HEADER'] = 'unknown_token'
        context = {'user': self.normal_user['name']}
        with nose.tools.assert_raises(ECAPINotAuthorized) as cm:
            helpers.call_action('dataset_request_create',
                                context=context,
                                **data_dict)
        os.environ['__CKANEXT_GLASGOW_AUTH_HEADER'] = ''

        assert 'task_id' in cm.exception.extra_msg

        task_id = cm.exception.extra_msg['task_id'][0]

        # Check that TaskStatus was actually created
        task_dict = helpers.call_action('task_status_show', id=task_id)

        eq_(task_dict['id'], task_id)
        eq_(task_dict['task_type'], 'dataset_request_create')
        eq_(task_dict['entity_type'], 'dataset')
        eq_(task_dict['key'], data_dict['name'])
        eq_(task_dict['state'], 'error')
        value = json.loads(task_dict['value'])
        assert 'data_dict' in value
        assert 'error' in value


def _get_mock_file_upload(file_name='test.csv'):

    mock_file = StringIO.StringIO()
    mock_file.write('File contents')

    mock_upload = cgi.FieldStorage()
    mock_upload.filename = 'test.csv'
    mock_upload.file = mock_file

    return mock_upload


class TestDatasetUpdate(object):
    def setup(self):
        self.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'normal_user',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       id='ec-org-id-1')

        context = {'local_action': True, 'user': 'normal_user'}
        data_dict = {
            'name': 'test_dataset',
            'owner_org': 'test_org',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'needs_approval': False,
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
        }

        self.dataset = helpers.call_action('package_create', context=context,
                                          **data_dict)

    def teardown(cls):
        helpers.reset_db()
        search.clear()

    @mock.patch('requests.request')
    def test_update(self, mock_request):
        # make the mock the result of calling requests.request(...)
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({'RequestId': 'req-id'}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {'RequestId': 'req-id'},
            }
        )

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

        nose.tools.assert_in('task_id',  request_dict)
        nose.tools.assert_equals(len(request_dict['task_id']), 36)

        nose.tools.assert_in('request_id', request_dict)

        # Check that TaskStatus was actually created
        task_dict = helpers.call_action('task_status_show',
                                        id=request_dict['task_id'])

        nose.tools.assert_dict_contains_subset(
            {
                'id':  request_dict['task_id'],
                'task_type': u'dataset_request_update',
                'entity_type': u'dataset',
                'state': u'sent',
            },
            task_dict
        )
        req_dict = json.loads(task_dict['value'])
        nose.tools.assert_equals('req-id', req_dict['request_id'])


class TestFileCreate(object):

    @classmethod
    def setup_class(cls):

        # Create test user
        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        # Create test org
        test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'normal_user',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       extras=[{'key': 'ec_api_id',
                                                'value': 1}])

        context = {'local_action': True, 'user': 'normal_user'}
        data_dict = {
            'name': 'test_dataset',
            'owner_org': 'test_org',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'needs_approval': False,
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
        }

        cls.dataset = helpers.call_action('package_create', context=context,
                                          **data_dict)

        # Start mock EC API
        run_mock_ec()

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_create(self):

        data_dict = {
            'package_id': self.dataset['id'],
            'name': 'Test File name',
            'description': 'Some longer description',
            'format': 'application/csv',
            'license_id': 'uk-ogl',
            'openness_rating': 3,
            'quality': 5,
            'standard_name': 'Test standard name',
            'standard_rating': 1,
            'standard_version': 'Test standard version',
            'creation_date': '2014-03-22T05:42:00',
            'ec_api_id': 3,
            'ec_api_dataset_id': 1,
            'upload': _get_mock_file_upload(),
        }

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('file_request_create',
                                           context=context,
                                           **data_dict)

        assert 'task_id' in request_dict
        eq_(len(request_dict['task_id']), 36)

        assert 'request_id' in request_dict
        # TODO: test format when known
        assert request_dict['request_id']

        # Check that TaskStatus was actually created
        task_dict = helpers.call_action('task_status_show',
                                        id=request_dict['task_id'])

        eq_(task_dict['id'], request_dict['task_id'])
        eq_(task_dict['task_type'], 'file_request_create')
        eq_(task_dict['entity_type'], 'file')
        assert self.dataset['id'] in task_dict['key']
        eq_(task_dict['state'], 'sent')
        assert 'data_dict' in json.loads(task_dict['value'])

    def test_create_can_use_dataset_id(self):

        data_dict = {
            'dataset_id': self.dataset['id'],
            'name': 'Test File name',
            'description': 'Some longer description',
            'format': 'application/csv',
            'license_id': 'uk-ogl',
            'openness_rating': 3,
            'quality': 5,
            'standard_name': 'Test standard name',
            'standard_rating': 1,
            'standard_version': 'Test standard version',
            'creation_date': '2014-03-22T05:42:00',
            'ec_api_id': 3,
            'ec_api_dataset_id': 1,
            'upload': _get_mock_file_upload(),
        }

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('file_request_create',
                                           context=context,
                                           **data_dict)

        assert 'task_id' in request_dict
        assert 'request_id' in request_dict

    def test_create_with_url(self):

        data_dict = {
            'dataset_id': self.dataset['id'],
            'name': 'Test File name',
            'url': 'http://some.file.org',
            'description': 'Some longer description',
            'format': 'application/csv',
            'license_id': 'uk-ogl',
            'openness_rating': 3,
            'quality': 5,
            'standard_name': 'Test standard name',
            'standard_rating': 1,
            'standard_version': 'Test standard version',
            'creation_date': '2014-03-22T05:42:00',
            'ec_api_id': 3,
            'ec_api_dataset_id': 1,
        }

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('file_request_create',
                                           context=context,
                                           **data_dict)

        assert 'task_id' in request_dict
        assert 'request_id' in request_dict

    def test_create_no_dataset_id(self):

        data_dict = {
            'name': 'Test File name',
            'description': 'Some longer description',
            'format': 'application/csv',
            'license_id': 'uk-ogl',
            'openness_rating': 3,
            'quality': 5,
            'standard_name': 'Test standard name',
            'standard_rating': 1,
            'standard_version': 'Test standard version',
            'creation_date': '2014-03-22T05:42:00',
        }

        context = {'user': self.normal_user['name']}
        nose.tools.assert_raises(p.toolkit.ValidationError,
                                 helpers.call_action,
                                 'file_request_create',
                                 context=context, **data_dict)

    def test_create_validation_errors(self):

        data_dict = {
            'package_id': self.dataset['id'],
            'name': 'a' * 256,
            'format': 'application/csv',
            'license_id': 'uk-ogl',
            'openness_rating': 'a',
            'quality': 5,
            'standard_name': 'Test standard name',
            'standard_rating': 1,
            'standard_version': 'Test standard version',
            'creation_date': '2014-03-22T05:42:00',
        }

        context = {'user': self.normal_user['name']}
        nose.tools.assert_raises(p.toolkit.ValidationError,
                                 helpers.call_action,
                                 'file_request_create',
                                 context=context, **data_dict)

    def test_create_dataset_does_not_exist(self):

        data_dict = {
            'package_id': 'unknown-dataset',
            'name': 'Test File name',
            'description': 'Some longer description',
            'format': 'application/csv',
            'license_id': 'uk-ogl',
            'openness_rating': 3,
            'quality': 5,
            'standard_name': 'Test standard name',
            'standard_rating': 1,
            'standard_version': 'Test standard version',
            'creation_date': '2014-03-22T05:42:00',
        }

        context = {'user': self.normal_user['name']}
        nose.tools.assert_raises(p.toolkit.ObjectNotFound,
                                 helpers.call_action,
                                 'file_request_create',
                                 context=context, **data_dict)
        

class TestFileUpdate(object):
    def setup(self):
        helpers.reset_db()
        search.clear()
        self.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'normal_user',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       id='ec-org-id-1')

        context = {'local_action': True, 'user': 'normal_user'}
        data_dict = {
            'name': 'test_dataset',
            'owner_org': 'test_org',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'needs_approval': False,
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
        }

        self.dataset = helpers.call_action('package_create', context=context,
                                          **data_dict)

        self.resource = helpers.call_action('resource_create', context=context,
                                            package_id=self.dataset['id'],
                                            name='test_file',
                                            description='test file description',
                                            format='csv',
                                            url='http://test.com')

    def teardown(cls):
        helpers.reset_db()
        search.clear()

    @mock.patch('requests.request')
    def test_update(self, mock_request):
        # make the mock the result of calling requests.request(...)
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({'RequestId': 'req-id'}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {'RequestId': 'req-id'},
            }
        )

        resource = helpers.call_action('resource_show', id=self.resource['id'])
        resource['description'] = 'updated description'
        resource['package_id'] = self.dataset['id']
        result = helpers.call_action('resource_update',
                                     context={'user': 'normal_user'},
                                     **resource)
        #check a task was correctly created
        task = helpers.call_action('task_status_show', id=result['task_id'])
        nose.tools.assert_equals('file_request_update', task['task_type'])
        nose.tools.assert_equals('file', task['entity_type'])
        nose.tools.assert_equals('req-id',
                                 json.loads(task['value'])['request_id'])


class TestFileVersions(object):
    @classmethod
    def setup_class(cls):

        # Create test user
        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        # Create test org
        test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'normal_user',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       extras=[{'key': 'ec_api_id',
                                                'value': 1}])

        context = {'local_action': True, 'user': 'normal_user'}
        data_dict = {
            'name': 'test_dataset-version',
            'owner_org': 'test_org',
            'title': 'Test Dataset Version',
            'notes': 'Some longer description',
            'needs_approval': False,
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
            'ec_api_id': 1,
            'ec_api_org_id': 1,
        }

        pkg = helpers.call_action('package_create', context=context,
                                          **data_dict)

        pkg['resources'] = [{
                'package_id': pkg['id'],
                'name': 'test_resource',
                'description': 'description',
                'format': 'csv',
                'url': 'http//test.com',
                'ec_api_id': '1',
            }
        ]

        context = {'local_action': True, 'user': 'normal_user'}
        cls.dataset = helpers.call_action('package_update', context=context,
                                          **pkg)


        # Start mock EC API
        run_mock_ec()

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_resource_versions_show(self):
        res = self.dataset['resources'][0]
        versions = helpers.call_action('resource_version_show',
                                       package_id=self.dataset['id'],
                                       resource_id=res['id'])

        expected_output = {
            'creation_date': u'1966-05-29T17:51:20',
            'description': u'test_description',
            'format': u'leannonvonrueden/bechtelarfritsch',
            'license_id': 'license',
            'name': u'Voluptates ex non quo itaque est quidem praesentium',
            'openness_rating': u'1',
            'quality': u'2',
            'standard_name': u'Accusamus aspernatur ut minima rem natus hic expedita voluptatibus',
            'standard_rating': u'4',
            'standard_version': u'7.4.30',
            'version': u'3afb06b1-4331-4abd-b88e-055492e21bab'
        }
        version = versions[0]
        nose.tools.assert_equals(sorted(expected_output.items()),
                                 sorted(version.items()))


class TestCheckForTaskStatusUpdate(object):
    @classmethod
    def setup_class(cls):

        # Create test user
        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        # Create test org
        test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'normal_user',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       extras=[{'key': 'ec_api_id',
                                                'value': 1}])

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    @mock.patch('requests.request')
    def test_update(self, mock_request):
        # setup a mock response from the EC API platform
        mock_result = mock.Mock()
        mock_result.status_code = 200
        mock_result.json.return_value = {
            'Operations': [
                {
                    'AuditId': 998,
                    'RequestId': 'D3C86B10-90F8-4CA6-A943-1404FB6C06BF',
                    'Timestamp': '2014-05-21T00:00:00',
                    'AuditType': 'FileCreateRequested',
                    'Command': 'CreateFile',
                    'ObjectType': 'File',
                    'OperationState': 'InProgress',
                    'Component': 'DataCollection',
                    'Owner': 'Admin',
                    'Message': 'File Creation request started',
                    'CustomProperties': [
                        {   
                            'OrganisationId': '1',
                            'DatasetId': '1',
                            }
                        ]
                    },
                {
                    'AuditId': 1000,
                    'RequestId': 'D3C86B10-90F8-4CA6-A943-1404FB6C06BF',
                    'Timestamp': '2014-05-21T00:00:00',
                    'AuditType': 'VirusScanThreatNotDetected',
                    'Command': 'CreateFile',
                    'ObjectType': 'File',
                    'OperationState': 'InProgress',
                    'Component': 'Antivirus',
                    'Owner': 'Admin',
                    'Message': 'Anti Virus scan complete',
                    'CustomProperties': [
                        {   
                            'OrganisationId': '1',
                            'DatasetId': '1',
                            }
                        ]
                    },
                {
                    'AuditId': 1005,
                    'RequestId': 'D3C86B10-90F8-4CA6-A943-1404FB6C06BF',
                    'Timestamp': '2014-05-21T00:00:10',
                    'AuditType': 'FileCreated',
                    'Command': 'CreateFile',
                    'ObjectType': 'File',
                    'OperationState': 'Succeeded',
                    'Component': 'DataPublication',
                    'Owner': 'Admin',
                    'Message': 'File Create Operation completed',
                    'CustomProperties': [
                        {   
                            'OrganisationId': '1',
                            'DatasetId': '1',
                            'FileId': '2',
                            'Versionid': 'VERSION-ID',
                            }
                        ]
                    }
                ]
        }
        # make the mock the result of calling requests.request(...)
        mock_request.return_value = mock_result

        # Create a test task_status here, that will be checked against the
        # ec api
        ckan_data_dict = {
            'name': 'test_dataset',
            'owner_org': 'test_org',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'needs_approval': False,
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'tags': [
                {'name': 'Test tag 1'},
                {'name': 'Test tag 2'},
            ],
            'openness_rating': 3,
            'quality': 5,
            'published_on_behalf_of': 'Test published on behalf of',
            'usage_guidance': 'Test usage guidance',
            'category': 'Test category',
            'theme': 'Test theme',
            'standard_name': 'Test standard name',
            'standard_rating': 5,
            'standard_version': 'Test standard version',
        }

        task_status = helpers.call_action(
            'task_status_update',
            task_type='dataset_request_create',
            entity_type='dataset',
            entity_id='ent_1',
            key='test_dataset',
            value=json.dumps({
                'request_id': 'abc123',
                'data_dict': ckan_data_dict
            }),
            last_updated=datetime.datetime(2000, 1, 1),
        )
        
        # run our action that updates the task status
        helpers.call_action('check_for_task_status_update',
                            task_id=task_status['id'])

        # check the dataset was created
        dataset = helpers.call_action('package_show', 
                                      name_or_id='test_dataset')


class TestGetChangeRequest(object):
    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_update(self, mock_request, mock_token):
        mock_token.return_value = 'mock_token'
        # setup a mock response from the EC API platform
        mock_result = mock.Mock()
        mock_result.status_code = 200
        mock_result.json.return_value = [
            {
                'AuditId': 998,
                'RequestId': 'D3C86B10-90F8-4CA6-A943-1404FB6C06BF',
                'Timestamp': '2014-05-21T00:00:00',
                'AuditType': 'FileCreateRequested',
                'Command': 'CreateFile',
                'ObjectType': 'File',
                'OperationState': 'InProgress',
                'Component': 'DataCollection',
                'Owner': 'Admin',
                'Message': 'File Creation request started',
                'CustomProperties': [
                    {   
                        'OrganisationId': '1',
                        'DatasetId': '1',
                        }
                    ]
                },
            {
                'AuditId': 1000,
                'RequestId': 'D3C86B10-90F8-4CA6-A943-1404FB6C06BF',
                'Timestamp': '2014-05-21T00:00:00',
                'AuditType': 'VirusScanThreatNotDetected',
                'Command': 'CreateFile',
                'ObjectType': 'File',
                'OperationState': 'InProgress',
                'Component': 'Antivirus',
                'Owner': 'Admin',
                'Message': 'Anti Virus scan complete',
                'CustomProperties': [
                    {   
                        'OrganisationId': '1',
                        'DatasetId': '1',
                        }
                    ]
                },
            {
                'AuditId': 1005,
                'RequestId': 'D3C86B10-90F8-4CA6-A943-1404FB6C06BF',
                'Timestamp': '2014-05-21T00:00:10',
                'AuditType': 'FileCreated',
                'Command': 'CreateFile',
                'ObjectType': 'File',
                'OperationState': 'Succeeded',
                'Component': 'DataPublication',
                'Owner': 'Admin',
                'Message': 'File Create Operation completed',
                'CustomProperties': [
                    {   
                        'OrganisationId': '1',
                        'DatasetId': '1',
                        'FileId': '2',
                        'Versionid': 'VERSION-ID',
                        }
                    ]
                }
            ]
        # make the mock the result of calling requests.request(...)
        mock_request.return_value = mock_result

        result = helpers.call_action('get_change_request', id='dummy')

    def test_no_id_parameter(self):
        nose.tools.assert_raises(
            p.toolkit.ValidationError,
            helpers.call_action,
            'get_change_request'
        )

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    def test_service_to_service_access_token_error(self, mock_token):
        import ckanext.oauth2waad.plugin as oauth2waad_plugin
        mock_token.side_effect = oauth2waad_plugin.ServiceToServiceAccessTokenError()
        nose.tools.assert_raises(
            ECAPIError,
            helpers.call_action,
            'get_change_request',
            id='dummy'
        )

    @mock.patch('ckanext.oauth2waad.plugin.service_to_service_access_token')
    @mock.patch('requests.request')
    def test_non_json(self, mock_request, mock_token):
        mock_token.return_value = 'mock_token'

        mock_result = mock.Mock()
        mock_result.status_code = 200
        mock_result.json.side_effect = ValueError('Not JSON')
        mock_request.return_value = mock_result

        nose.tools.assert_raises(
            ECAPIError,
            helpers.call_action,
            'get_change_request',
            id='dummy'
        )


class TestChangelog(object):

    @classmethod
    def setup_class(cls):

        # Create sysadmin user
        cls.sysadmin_user = helpers.call_action('user_create',
                                                name='sysadmin_user',
                                                email='test@test.com',
                                                password='test',
                                                sysadmin=True)

        # Start mock EC API
        run_mock_ec()

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_changelog_show(self):

        data_dict = {}
        context = {'user': self.sysadmin_user['name']}
        audit_list = helpers.call_action('changelog_show',
                                         context=context,
                                         **data_dict)

        eq_(len(audit_list), 3)

        audit_dict = audit_list[0]

        assert 'AuditId' in audit_dict
        assert 'Command' in audit_dict
        assert 'ObjectType' in audit_dict
        assert audit_dict['ObjectType'] in ('Dataset', 'File', 'Organisation')
        assert 'RequestId' in audit_dict
        assert 'Timestamp' in audit_dict

    def test_changelog_show_starting_id(self):

        data_dict = {
            'audit_id': 1010,
        }
        context = {'user': self.sysadmin_user['name']}
        audit_list = helpers.call_action('changelog_show',
                                         context=context,
                                         **data_dict)

        eq_(len(audit_list), 2)

    def test_changelog_show_top_results(self):

        data_dict = {
            'top': 2,
        }
        context = {'user': self.sysadmin_user['name']}
        audit_list = helpers.call_action('changelog_show',
                                         context=context,
                                         **data_dict)

        eq_(len(audit_list), 2)

    def test_changelog_show_starting_and_top_results(self):

        data_dict = {
            'audit_id': 1010,
            'top': 1,
        }
        context = {'user': self.sysadmin_user['name']}
        audit_list = helpers.call_action('changelog_show',
                                         context=context,
                                         **data_dict)

        eq_(len(audit_list), 1)

    def test_changelog_show_object_type(self):

        data_dict = {
            'object_type': 'File',
        }
        context = {'user': self.sysadmin_user['name']}
        audit_list = helpers.call_action('changelog_show',
                                         context=context,
                                         **data_dict)

        eq_(len(audit_list), 1)

        eq_(audit_list[0]['ObjectType'], 'File')


class TestOrganizationCreate(object):
    def setup(self):
        self.normal_user = helpers.call_action('user_create',
                                               name='normal_user',
                                               email='test@test.com',
                                               password='test')

    def teardown(cls):
        helpers.reset_db()

    @mock.patch('requests.request')
    def test_organization(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {
                    'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'
                },
            }
        )
        data_dict = {
            'name': 'test_org',
            'needs_approval': False
        }
        request_dict = helpers.call_action('organization_request_create',
                                          context={'user': 'normal_user'},
                                          **data_dict)

        nose.tools.assert_in('task_id', request_dict)
        nose.tools.assert_in('request_id', request_dict)

        task_dict = helpers.call_action('task_status_show',
                                        id=request_dict['task_id'])
        nose.tools.assert_dict_contains_subset(
            {
                'task_type': u'organization_request_create',
                'entity_type': u'organization',
                'state': u'sent',
                'error': None
            },
            task_dict
        )

class TestOrganizationUpdate(object):
    def setup(self):
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

    def teardown(cls):
        helpers.reset_db()

    @mock.patch('requests.request')
    def test_update(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {
                    'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'
                },
            }
        )
        data_dict = {
            'id': self.test_org['id'],
            'name': 'test_updated_org',
            'needs_approval': False
        }
        request_dict = helpers.call_action('organization_request_update',
                                          context={'user': 'normal_user'},
                                          **data_dict)
        nose.tools.assert_in('task_id', request_dict)
        nose.tools.assert_in('request_id', request_dict)

        task_dict = helpers.call_action('task_status_show',
                                        id=request_dict['task_id'])
        nose.tools.assert_dict_contains_subset(
            {
                'task_type': u'organization_request_update',
                'entity_type': u'organization',
                'state': u'sent',
                'error': None
            },
            task_dict
        )

class TestUserRoleUpdate(object):
    def setup(self):
        self.org_owner = helpers.call_action('user_create',
                                               name='org_owner',
                                               email='test@test.com',
                                               password='test')

        self.normal_user = helpers.call_action('user_create',
                                               name='normal_user',
                                               email='test@test.com',
                                               password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'org_owner',
                                           'local_action': True,
                                       },
                                       name='test_org')

    def teardown(cls):
        helpers.reset_db()

    @mock.patch('requests.request')
    def test_make_user_member(self, mock_request):
        '''test adding a member goes through ckan only'''
        mock_request.return_value = mock.Mock(
            status_code=404,
            content=json.dumps({'UserId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'}),
            **{
                'raise_for_status.side_effect': requests.exceptions.HTTPError(),
                'json.return_value': {
                    'UserId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'
                },
            }
        )
        data_dict = {
            'id': self.test_org['id'],
            'username': 'normal_user',
            'role': 'member',
        }

        helpers.call_action('organization_member_create',
                            context={'user': 'org_owner'},
                            **data_dict)

        # check normal member was created
        members = helpers.call_action('member_list',
                                      id=self.test_org['id'])

        member_ids = set([i[0] for i in members])
        nose.tools.assert_in(self.normal_user['id'], member_ids)


    @mock.patch('requests.request')
    def test_making_ckan_user_into_org_editor_errors(self, mock_request):
        '''test that making user an org editor

        a standard user being made into an editor should raise a 
        validation error'''
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({'UserId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {
                    'UserId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'
                },
            }
        )

        data_dict = {
            'id': self.test_org['id'],
            'username': 'normal_user',
            'role': 'editor',
        }

        nose.tools.assert_raises(
            p.toolkit.ValidationError,
            helpers.call_action,
            'organization_member_create',
            context={'user': 'org_owner'},
            **data_dict)


    @mock.patch('ckan.lib.helpers.flash_success')
    @mock.patch('requests.request')
    def test_make_ec_user_with_org_into_org_admin(self, mock_request, mock_flash):
        '''test that making user an org admin

        a ec user being made into an admin should send a request
        to the EC platform'''
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({
                'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d',
                'OrganisationId': self.test_org['id']}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {
                    'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d',
                    'OrganisationId': self.test_org['id'],
                },
            }
        )

        # mock out the flash_success helper to avoid problems with the beaker
        # session in tests
        mock_flash.return_value = None

        data_dict = {
            'id': self.test_org['id'],
            'username': 'normal_user',
            'role': 'admin',
        }

        request_dict = helpers.call_action('organization_member_create',
                                           context={'user': 'org_owner'},
                                           **data_dict)



        nose.tools.assert_in('task_id', request_dict)
        nose.tools.assert_in('request_id', request_dict)

        task_dict = helpers.call_action('task_status_show',
                                        id=request_dict['task_id'])
        nose.tools.assert_dict_contains_subset(
            {
                'task_type': u'member_update',
                'entity_type': u'organization',
                'state': u'sent',
                'error': None
            },
            task_dict
        )
        mock_request.assert_called_with(
            'PUT',
            '/UserRoles/Organisation/{}/User/{}'.format(self.test_org['id'],
                                                        self.normal_user['name']),
            verify=False,
            data='{{"NewOrganisationId": "{}", "UserRoles": {{"UserGroup": ["OrganisationAdmin"]}}}}'.format(self.test_org['id']),
            timeout=50,
            headers={
                'Content-Type': 'application/json', 'Authorization': 'Bearer tmp_auth_token'
            }
        )

    @mock.patch('ckan.lib.helpers.flash_success')
    @mock.patch('requests.request')
    def test_make_ec_user_without_org_into_an_org_admin(self, mock_request, mock_flash):
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {
                    'RequestId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d',
                },
            }
        )

        # mock out the flash_success helper to avoid problems with the beaker
        # session in tests
        mock_flash.return_value = None

        data_dict = {
            'id': self.test_org['id'],
            'username': 'normal_user',
            'role': 'admin',
        }

        request_dict = helpers.call_action('organization_member_create',
                                           context={'user': 'org_owner'},
                                           **data_dict)



        nose.tools.assert_in('task_id', request_dict)
        nose.tools.assert_in('request_id', request_dict)

        task_dict = helpers.call_action('task_status_show',
                                        id=request_dict['task_id'])
        nose.tools.assert_dict_contains_subset(
            {
                'task_type': u'member_update',
                'entity_type': u'organization',
                'state': u'sent',
                'error': None
            },
            task_dict
        )
        mock_request.assert_called_with(
            'PUT',
            '/UserRoles/User/{}'.format(self.normal_user['name']),
            verify=False,
            data='{{"NewOrganisationId": "{}", "UserRoles": {{"UserGroup": ["OrganisationAdmin"]}}}}'.format(self.test_org['id']),
            timeout=50,
            headers={
                'Content-Type': 'application/json', 'Authorization': 'Bearer tmp_auth_token'
            }
        )

    @mock.patch('requests.request')
    def test_making_ec_user_editor_a_member_fails(self, mock_request):
        '''test that making an org editor a member

        a organization editor being made into an user should raise
        a validation error'''
        mock_request.return_value = mock.Mock(
            status_code=200,
            content=json.dumps({'UserId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'}),
            **{
                'raise_for_status.return_value': None,
                'json.return_value': {
                    'UserId': 'cc02730a-367d-45a6-9db3-6fc3dc5ca49d'
                },
            }
        )

        # make our normal_user and editor
        data_dict = {
            'id': self.test_org['id'],
            'username': 'normal_user',
            'role': 'editor',
        }

        request_dict = helpers.call_action('organization_member_create',
                                           context={
                                               'user': 'org_owner',
                                               'local_action': True,
                                            },
                                           **data_dict)

        # make a call to ec platform to make editor a member
        data_dict = {
            'id': self.test_org['id'],
            'username': 'normal_user',
            'role': 'member',
        }

        nose.tools.assert_raises(
            p.toolkit.ValidationError,
            helpers.call_action,
            'organization_member_create',
            context={'user': 'org_owner'},
            **data_dict)
