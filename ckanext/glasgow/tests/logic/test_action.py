import cgi
import os
import StringIO
import json

import nose

from pylons import config

import ckan.model as model
import ckan.plugins as p
import ckan.new_tests.helpers as helpers

from ckanext.glasgow.logic.action import (
    _get_api_endpoint,
    _create_task_status,
    _update_task_status_success,
    _update_task_status_error,
    ECAPINotAuthorized,
    )

from ckanext.glasgow.tests import run_mock_ec


eq_ = nose.tools.eq_


class TestGetAPIEndpoint(object):

    @classmethod
    def setup_class(cls):

        cls._base_write_api = 'https://base.write.api/'
        cls._base_read_api = 'https://base.read.api/'

        config['ckanext.glasgow.data_collection_api'] = cls._base_write_api
        config['ckanext.glasgow.metadata_api'] = cls._base_read_api

    def test_get_api_endpoint(self):
        base_api = self._base_write_api.rstrip('/')

        eq_(_get_api_endpoint('dataset_request_create'),
            ('POST', base_api + '/Datasets/Organisation/{organization_id}'))
        eq_(_get_api_endpoint('dataset_request_update'),
            ('PUT', base_api + '/Datasets/Organisation/{organization_id}/Dataset/{dataset_id}'))
        eq_(_get_api_endpoint('file_request_create'),
            ('POST', base_api + '/Files/Organisation/{organization_id}/Dataset/{dataset_id}'))
        eq_(_get_api_endpoint('file_request_update'),
            ('PUT', base_api + '/Files/Organisation/{organization_id}/Dataset/{dataset_id}'))


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
                                       context={'user': 'normal_user'},
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
                                       context={'user': 'normal_user'},
                                       name='test_org',
                                       extras=[{'key': 'ec_api_id',
                                                'value': 1}])

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
