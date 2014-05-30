import json
import datetime
import uuid

import requests
from sqlalchemy import or_

from pylons import config

import ckan.model as model
import ckan.plugins as p
from ckan.lib.navl.dictization_functions import validate
import ckan.lib.dictization.model_dictize as model_dictize

import ckanext.glasgow.logic.schema as custom_schema

get_action = p.toolkit.get_action
check_access = p.toolkit.check_access


def _make_uuid():
    return unicode(uuid.uuid4())


def _get_api_endpoint(operation):
    '''
    Returns the relevant EC API endpoint for a particular operation

    Uses the 'ckanext.glasgow.ec_api' configuration option as a base.
    This function can be expanded in the future to support different APIs
    and extra endpoints

    :param operation: the operation we need to know the endpoint for
                      (eg 'dataset_request_create')
    :type operation: string

    :returns: a tuple, the first member being the HTTP method, and the
              second the URL.
    :rtype: tuple
    '''

    base = config.get('ckanext.glasgow.ec_api', '').rstrip('/')

    if operation == 'dataset_request_create':
        method = 'POST'
        url = '/datasets'
    elif operation == 'dataset_request_update':
        method = 'PUT'
        url = '/datasets'
    elif operation == 'resource_request_create':
        method = 'POST'
        url = '/files'
    elif operation == 'resource_request_update':
        method = 'PUT'
        url = '/files'

    return method, '{0}{1}'.format(base, url)


def pending_task_for_dataset(context, data_dict):
    '''
    Returns the most recent pending request for a particular dataset

    Returns the most recent TaskStatus with a state of 'new' or 'sent'.
    Datasets can be identified by id or name.

    :param id: Dataset id (optional if name provided)
    :type operation: string
    :param name: Dataset name (optional if id provided)
    :type operation: string

    :returns: a task status dict if found, None otherwise.
    :rtype: dict
    '''

    p.toolkit.check_access('pending_task_for_dataset', context, data_dict)

    id = data_dict.get('id') or data_dict.get('name')

    model = context.get('model')
    task = model.Session.query(model.TaskStatus) \
        .filter(model.TaskStatus.entity_type == 'dataset') \
        .filter(or_(model.TaskStatus.state == 'new',
                model.TaskStatus.state == 'sent')) \
        .filter(or_(
                model.TaskStatus.key == id,
                model.TaskStatus.entity_id == id,
                )) \
        .order_by(model.TaskStatus.last_updated.desc()) \
        .first()

    if task:
        return model_dictize.task_status_dictize(task, context)
    else:
        return None


def dataset_request_create(context, data_dict):
    '''
    Requests the creation of a dataset to the EC Data Collection API

    This function accepts the same parameters as the default
    `package_create` and will run the same validation, but instead of
    creating the dataset in CKAN will store the submitted data in the
    `task_status` table and forward it to the Data Collection API.

    :raises: :py:exc:`~ckan.plugins.toolkit.ValidationError` if the
        validation of the submitted data didn't pass, or the EC API returned
        an error. In this case, the exception will contain the following:
        {
            'status': status_code, # HTTP status code returned by the EC API
            'content': response # JSON response returned by the EC API
        }

    :raises: :py:exc:`~ckan.plugins.toolkit.NotAuthorized` if the
        user is not authorized to perform the operaion, or the EC API returned
        an authorization error. In this case, the exception will contain the
        following:
        {
            'status': status_code, # HTTP status code returned by the EC API
            'content': response # JSON response returned by the EC API
        }


    :returns: a dictionary with the CKAN `task_id` and the EC API `request_id`
    :rtype: dictionary

    '''

    # TODO: refactor to reuse code across updates and file creation/udpate

    # Check access

    check_access('dataset_request_create', context, data_dict)

    # Validate data_dict

    context.update({'model': model, 'session': model.Session})
    create_schema = custom_schema.create_package_schema()

    validated_data_dict, errors = validate(data_dict, create_schema, context)

    if errors:
        model.Session.rollback()
        raise p.toolkit.ValidationError(errors)

    # Create a task status entry with the validated data

    task_dict = _create_task_status(context,
                                    task_type='dataset_request_create',
                                    # This will be used as dataset id
                                    entity_id=_make_uuid(),
                                    entity_type='dataset',
                                    # This will be used for validating datasets
                                    key=validated_data_dict['name'],
                                    value=json.dumps(
                                        {'data_dict': validated_data_dict})
                                    )

    # Convert payload from CKAN to EC API spec

    ec_dict = custom_schema.convert_ckan_dataset_to_ec_dataset(data_dict)

    # Send request to EC Data Collection API

    method, url = _get_api_endpoint('dataset_request_create')

    # TODO: Authenticate request
    headers = {
        'Authorization': 'tmp_token',
        'Content-Type': 'application/json',
    }

    response = requests.request(method, url,
                                data=json.dumps(ec_dict),
                                headers=headers,
                                )

    status_code = response.status_code

    if not response.content:
        raise p.toolkit.ValidationError('Empty content')

    content = response.json()

    # Check status codes

    if status_code != 200:
        error_dict = {
            'status': status_code,
            'content': content
        }
        task_dict = _update_task_status_error(context, task_dict, error_dict)

        if status_code == 401:
            raise p.toolkit.NotAuthorized(error_dict)
        else:
            raise p.toolkit.ValidationError(error_dict)

    # Store data in task status table

    request_id = content.get('RequestId')
    task_dict = _update_task_status_success(context, task_dict, {
        'data_dict': validated_data_dict,
        'request_id': request_id,
    })

    # Return task id to access it later and the request id returned by the
    # EC Metadata API

    return {
        'task_id': task_dict['id'],
        'request_id': request_id,
    }


def _create_task_status(context, task_type, entity_id, entity_type, key,
                        value):

    context.update({'ignore_auth': True})

    if not isinstance(value, basestring):
        value = json.dumps(value)

    task_dict = {
        'task_type': task_type,
        'entity_id': entity_id,
        'entity_type': entity_type,
        'key': key,
        'value': value,
        'state': 'new',
        'last_updated': datetime.datetime.now(),
    }
    task_dict = get_action('task_status_update')(context, task_dict)

    return task_dict


def _update_task_status_success(context, task_dict, value):

    context.update({'ignore_auth': True})

    if not isinstance(value, basestring):
        value = json.dumps(value)

    task_dict['state'] = 'sent'
    task_dict['value'] = value
    task_dict['last_updated'] = datetime.datetime.now()

    task_dict = get_action('task_status_update')(context, task_dict)

    return task_dict


def _update_task_status_error(context, task_dict, value):

    context.update({'ignore_auth': True})

    if not isinstance(value, basestring):
        value = json.dumps(value)

    task_dict['state'] = 'error'
    task_dict['value'] = value
    task_dict['last_updated'] = datetime.datetime.now()

    task_dict = get_action('task_status_update')(context, task_dict)

    return task_dict


def dataset_request_update(context, data_dict):
    pass
