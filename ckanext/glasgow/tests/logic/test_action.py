from threading import Thread
import json

import nose

from pylons import config

import ckan.model as model
import ckan.new_tests.helpers as helpers

from ckanext.glasgow.logic.action import (
    _get_api_endpoint,
    _create_task_status,
    _update_task_status_success,
    _update_task_status_error,
    )
from ckanext.glasgow.tests.mock_ec import run as run_mock_ec


eq_ = nose.tools.eq_


class TestGetAPIEndpoint(object):

    @classmethod
    def setup(cls):

        cls._base_api = 'https://base.api/'

        config['ckanext.glasgow.ec_api'] = cls._base_api

    def test_get_api_endpoint(self):
        base_api = self._base_api.rstrip('/')

        eq_(_get_api_endpoint('dataset_request_create'),
            ('POST', base_api + '/datasets'))
        eq_(_get_api_endpoint('dataset_request_update'),
            ('PUT', base_api + '/datasets'))
        eq_(_get_api_endpoint('resource_request_create'),
            ('POST', base_api + '/files'))
        eq_(_get_api_endpoint('resource_request_update'),
            ('PUT', base_api + '/files'))


class TestTaskStatusHelpers(object):

    @classmethod
    def setup_class(cls):
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

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           name='test_dataset_name'
                                           )

        eq_(pending_task['id'], task_dict['id'])

    def test_pending_task_for_dataset_by_id(self):

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           id='test_dataset_id'
                                           )

        eq_(pending_task['id'], task_dict['id'])

    def test_pending_task_for_dataset_success_found(self):

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        task_dict = _update_task_status_success({'user': 'test'},
                                                task_dict=task_dict,
                                                value='test_value_updated'
                                                )

        pending_task = helpers.call_action('pending_task_for_dataset',
                                           id='test_dataset_id'
                                           )

        eq_(pending_task['id'], task_dict['id'])

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
    def setup(cls):

        # Create test user
        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        # Start mock EC API
        def run():
            run_mock_ec(port=7071, debug=False)

        t = Thread(target=run)
        t.daemon = True
        t.start()

        config['ckanext.glasgow.ec_api'] = 'http://0.0.0.0:7071'

    @classmethod
    def teardown(cls):
        helpers.reset_db()

    def test_create(self):

        data_dict = {
            'name': 'test-dataset',
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
        eq_(task_dict['state'], 'new')
        assert 'data_dict' in json.loads(task_dict['value'])
