import os
import cgi
import logging
import json
import datetime
import uuid
import re

import dateutil.parser
import requests
from sqlalchemy import or_

from pylons import config, session

import ckan.model as model
import ckan.plugins as p
from ckan.lib.navl.dictization_functions import validate
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.logic.action as core_actions
from ckan.logic import ActionError

import ckanext.oauth2waad.plugin as oauth2


import ckanext.glasgow.logic.schema as custom_schema


log = logging.getLogger(__name__)

get_action = p.toolkit.get_action
check_access = p.toolkit.check_access


class ECAPIError(ActionError):
    pass


class ECAPINotAuthorized(ActionError):
    pass


class ECAPIValidationError(p.toolkit.ValidationError):
    pass


def _make_uuid():
    return unicode(uuid.uuid4())


def _get_api_auth_token():
    '''
    Use the auth_token obtained when logging in with the WAAD credentials

    This is stored in the Pylons session
    TODO: refresh it when expired

    :returns: an auth_token value ready to be used in an `Authorization`
              header (ie following the Bearer scheme)
    :rtype: string

    '''

    token = None

    try:
        token = session.get('ckanext-oauth2waad-access-token')

    except TypeError:
        # No session (eg tests or command line)
        pass

        # Allow token to be set from an env var. Useful for the tests.
        token = os.environ.get('__CKANEXT_GLASGOW_AUTH_HEADER', None)

    if not token:

        # From this onwards it is all fake, it's just temporary maintained in
        # case proper integration with WAAD is not working

        token = 'tmp_auth_token'

        tmp_token_file = config.get('ckanext.glasgow.tmp_auth_token_file')
        if tmp_token_file:
            try:
                with open(tmp_token_file, 'r') as f:
                    token = f.read().strip('\n')
            except IOError:
                log.critical('Temp auth token file not found: {0}'
                             .format(tmp_token_file))

    if not token.startswith('Bearer '):
        token = 'Bearer ' + token

    return token


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

    write_base = config.get('ckanext.glasgow.data_collection_api', '').rstrip('/')
    read_base = config.get('ckanext.glasgow.metadata_api', '').rstrip('/')

    if operation == 'dataset_request_create':
        method = 'POST'
        path = '/Datasets/Organisation/{organization_id}'
    elif operation == 'dataset_request_update':
        method = 'PUT'
        path = '/Datasets/Organisation/{organization_id}/Dataset/{dataset_id}'
    elif operation == 'file_request_create':
        method = 'POST'
        path = '/Files/Organisation/{organization_id}/Dataset/{dataset_id}'
    elif operation == 'file_request_update':
        method = 'PUT'
        path = '/Files/Organisation/{organization_id}/Dataset/{dataset_id}'
    elif operation == 'organization_show':
        method = 'GET'
        path = '/Metadata/Organisation/{organization_id}'
    elif operation == 'dataset_show':
        method = 'GET'
        path = '/Metadata/Organisation/{organization_id}/Dataset/{dataset_id}'
    elif operation == 'file_show':
        method = 'GET'
        path = '/Metadata/Organisation/{organization_id}/Dataset/{dataset_id}/File/{file_id}'
    elif operation == 'file_version_show':
        method = 'GET'
        path = '/Metadata/Organisation/{organization_id}/Dataset/{dataset_id}/File/{file_id}/Versions'
    elif operation == 'request_status_show':
        method = 'GET'
        path = '/ChangeLog/RequestStatus/{request_id}'
    elif operation == 'changelog_show':
        method = 'GET'
        path = '/ChangeLog/RequestChanges'
    else:
        return None, None

    base = write_base if method in ('POST', 'PUT') else read_base

    return method, '{0}{1}'.format(base, path)


def _get_ec_api_org_id(ckan_org_id):
    # Get EC API id from parent organization
    org_dict = p.toolkit.get_action('organization_show')({}, {
        'id': ckan_org_id})

    ec_api_org_id = org_dict.get('ec_api_id')

    # TODO: remove once the orgs use a proper schema
    if not ec_api_org_id:
        values = [e['value'] for e in org_dict.get('extras', [])
                  if e['key'] == 'ec_api_id']
        ec_api_org_id = values[0] if len(values) else None

    return ec_api_org_id


@p.toolkit.side_effect_free
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


def pending_files_for_dataset(context, data_dict):
    '''
    Returns list of pending file tasks for a dataset

    Returns the most recent TaskStatus with a state of 'new' or 'sent'.
    Datasets can be identified by id or name.

    :param id: Dataset id (optional if name provided)
    :type operation: string

    :returns: a task status dict if found, None otherwise.
    :rtype: dict
    '''

    p.toolkit.check_access('pending_task_for_dataset', context, data_dict)

    id = data_dict.get('id')
    name = data_dict.get('name')
    try:
        dataset_dict = p.toolkit.get_action('package_show')(context,
            {'name_or_id': id or name})
    except p.toolkit.NotFound:
        raise p.toolkit.ValidationError(['Dataset not found'])

    model = context.get('model')
    tasks = model.Session.query(model.TaskStatus) \
        .filter(model.TaskStatus.entity_type == 'file') \
        .filter(or_(model.TaskStatus.state == 'new',
                model.TaskStatus.state == 'sent')) \
        .filter(or_(model.TaskStatus.key.like('{0}%'.format(dataset_dict['id'])),
                model.TaskStatus.key.like('{0}%'.format(dataset_dict['name'])))) \
        .order_by(model.TaskStatus.last_updated.desc())

    results = []
    for task in tasks:
        task_dict = model_dictize.task_status_dictize(task, context)
        results.append(task_dict)
    return results


def package_create(context, data_dict):

    if data_dict.get('__local_action', False):
        context['local_action'] = True
        data_dict.pop('__local_action', None)

    if (context.get('local_action', False) or
            data_dict.get('type') == 'harvest'):

        return core_actions.create.package_create(context, data_dict)

    else:

        return p.toolkit.get_action('dataset_request_create')(context,
                                                              data_dict)


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
        raise p.toolkit.ValidationError(errors)

    # Get parent org EC API id
    ec_api_org_id = validated_data_dict.get('ec_api_org_id') or \
                    _get_ec_api_org_id(validated_data_dict['owner_org'])

    if not ec_api_org_id:
        raise p.toolkit.ValidationError(
            ['Could not get EC API id for parent organization'])

    # Create a task status entry with the validated data

    task_dict = _create_task_status(context,
                                    task_type='dataset_request_create',
                                    # This will be used as dataset id
                                    entity_id=_make_uuid(),
                                    entity_type='dataset',
                                    # This will be used for validating datasets
                                    key=validated_data_dict['name'],
                                    value=json.dumps(
                                        {'data_dict': data_dict})
                                    )

    # Convert payload from CKAN to EC API spec

    ec_dict = custom_schema.convert_ckan_dataset_to_ec_dataset(
        validated_data_dict)

    # Send request to EC Data Collection API

    method, url = _get_api_endpoint('dataset_request_create')

    url = url.format(
        organization_id=ec_api_org_id
    )

    headers = {
        'Authorization': _get_api_auth_token(),
        'Content-Type': 'application/json',
    }

    try:
        response = requests.request(method, url,
                                    data=json.dumps(ec_dict),
                                    headers=headers,
                                    )
    except requests.exceptions.RequestException, e:
        error_dict = {
            'message': ['Request exception: {0}'.format(e)],
            'task_id': [task_dict['id']]
        }
        task_dict = _update_task_status_error(context, task_dict, {
            'data_dict': validated_data_dict,
            'error': error_dict
        })
        raise p.toolkit.ValidationError(error_dict)

    status_code = response.status_code

    if not response.content:
        raise p.toolkit.ValidationError(['Empty content'])

    content = response.json()

    # Check status codes

    if status_code != 200:
        error_dict = {
            'message': ['The CTPEC API returned an error code'],
            'status': [status_code],
            'content': [content],
            'task_id': [task_dict['id']]
        }
        task_dict = _update_task_status_error(context, task_dict, {
            'data_dict': data_dict,
            'error': error_dict
        })

        if status_code == 401:
            raise ECAPINotAuthorized(error_dict)
        else:
            raise p.toolkit.ValidationError(error_dict)

    # Store data in task status table

    request_id = content.get('RequestId')
    task_dict = _update_task_status_success(context, task_dict, {
        'data_dict': data_dict,
        'request_id': request_id,
    })

    # Return task id to access it later and the request id returned by the
    # EC Metadata API

    return {
        'task_id': task_dict['id'],
        'request_id': request_id,
        # This is required by the core controller to do the redirect
        'name': validated_data_dict['name'],
    }


def resource_create(context, data_dict):

    if data_dict.get('__local_action', False):
        context['local_action'] = True
        data_dict.pop('__local_action', None)
    if context.get('local_action', False):

        return core_actions.create.resource_create(context, data_dict)

    else:

        return p.toolkit.get_action('file_request_create')(context,
                                                           data_dict)


def file_request_create(context, data_dict):
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

    # Check if parent dataset exists

    if data_dict.get('dataset_id'):
        data_dict['package_id'] = data_dict['dataset_id']
    package_id = p.toolkit.get_or_bust(data_dict, 'package_id')

    try:
        dataset_dict = p.toolkit.get_action('package_show')(context,
                                                            {'id': package_id})
    except p.toolkit.ObjectNotFound:
        raise p.toolkit.ObjectNotFound('Dataset not found')

    # Check access

    check_access('file_request_create', context, data_dict)

    # Validate data_dict

    context.update({'model': model, 'session': model.Session})
    create_schema = custom_schema.resource_schema()

    validated_data_dict, errors = validate(data_dict, create_schema, context)

    if errors:
        raise p.toolkit.ValidationError(errors)

    # Get parent org and dataset EC API ids

    ec_api_org_id = validated_data_dict.get('ec_api_org_id') or \
                    _get_ec_api_org_id(dataset_dict['owner_org'])
    ec_api_dataset_id = validated_data_dict.get('ec_api_dataset_id') or \
                    dataset_dict['ec_api_id']

    if not ec_api_org_id:
        raise p.toolkit.ValidationError(
            ['Could not get EC API id for parent organization'])
    if not ec_api_dataset_id:
        raise p.toolkit.ValidationError(
            ['Could not get EC API id for parent dataset'])

    # Create a task status entry with the validated data

    key = '{0}@{1}'.format(validated_data_dict.get('package_id', 'file'),
                           datetime.datetime.now().isoformat())

    uploaded_file = data_dict.pop('upload', None)
    task_dict = _create_task_status(context,
                                    task_type='file_request_create',
                                    entity_id=_make_uuid(),
                                    entity_type='file',
                                    key=key,
                                    value=json.dumps(
                                        {'data_dict': data_dict})
                                    )

    # Convert payload from CKAN to EC API spec

    ec_dict = custom_schema.convert_ckan_resource_to_ec_file(
        validated_data_dict)

    # Send request to EC Data Collection API

    method, url = _get_api_endpoint('file_request_create')
    url = url.format(
        organization_id=ec_api_org_id,
        dataset_id=ec_api_dataset_id,
    )

    headers = {
        'Authorization': _get_api_auth_token(),
    }


    if isinstance(uploaded_file, cgi.FieldStorage):
        files = {
            'file': (uploaded_file.filename,
                     uploaded_file.file)
        }
        data = {
            'metadata': json.dumps(ec_dict)
        }
    else:
        headers['Content-Type'] = 'application/json'
        files = None
        data = json.dumps(ec_dict)

    try:
        response = requests.request(method, url,
                                    data=data,
                                    files=files,
                                    headers=headers,
                                    )
    except requests.exceptions.RequestException, e:
        error_dict = {
            'message': ['Request exception: {0}'.format(e)],
            'task_id': [task_dict['id']]
        }
        task_dict = _update_task_status_error(context, task_dict, {
            'data_dict': validated_data_dict,
            'error': error_dict
        })
        raise p.toolkit.ValidationError(error_dict)

    status_code = response.status_code

    if not response.content:
        raise p.toolkit.ValidationError(['Empty content'])

    content = response.json()

    # Check status codes

    if status_code != 200:
        error_dict = {
            'message': ['The CTPEC API returned an error code'],
            'status': [status_code],
            'content': [content],
        }
        # Log the details of the request to the error_dict when
        # stored to the task_status.
        task_error_dict = error_dict.copy()
        task_error_dict.update({
            'data': data,
            'url': [url],
            'headers': headers,
        })
        task_dict = _update_task_status_error(context, task_dict,
                                              task_error_dict)

        if status_code == 401:
            raise ECAPINotAuthorized(error_dict)
        else:
            raise p.toolkit.ValidationError(error_dict)

    # Store data in task status table

    request_id = content.get('RequestId')

    task_dict = _update_task_status_success(context, task_dict, {
        'data_dict': data_dict,
        'request_id': request_id,
    })

    # Return task id to access it later and the request id returned by the
    # EC Metadata API

    return {
        'task_id': task_dict['id'],
        'request_id': request_id,
        'name': None,
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

    _expire_task_status(context, task_dict['id'])

    return task_dict


def _update_task_status_error(context, task_dict, value):

    context.update({'ignore_auth': True})

    if not isinstance(value, basestring):
        value = json.dumps(value)

    task_dict['state'] = 'error'
    task_dict['value'] = value
    task_dict['last_updated'] = datetime.datetime.now()

    task_dict = get_action('task_status_update')(context, task_dict)

    _expire_task_status(context, task_dict['id'])

    return task_dict


def _expire_task_status(context, task_id):
    '''Expires a TaskStatus object from the current Session

    TaskStatus are generally updated twice in the same Session (first in
    `_create_task_status` and then in either `_update_task_status_error`
    or `_update_task_status_succes`. If we want functions calling the
    `dataset_request_create` action to access the latest version, we need to
    expire the object currently held in the Session.
    '''
    if not context.get('model'):
        return

    model = context['model']

    task = model.Session.query(model.TaskStatus).get(task_id)
    if task:
        model.Session.expire(task)


def package_update(context, data_dict):

    if data_dict.get('__local_action', False):
        context['local_action'] = True
        data_dict.pop('__local_action', None)

    if (context.get('local_action', False) or
            data_dict.get('type') == 'harvest'):

        return core_actions.update.package_update(context, data_dict)

    else:

        return p.toolkit.get_action('dataset_request_update')(context,
                                                              data_dict)


def dataset_request_update(context, data_dict):
    '''
    Requests the update of a dataset to the EC Data Collection API

    This function accepts the same parameters as the default
    `package_update` and will run the same validation, but instead of
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

    check_access('dataset_request_update', context, data_dict)

    # Validate data_dict

    context.update({'model': model, 'session': model.Session})
    create_schema = custom_schema.update_package_schema()

    validated_data_dict, errors = validate(data_dict, create_schema, context)

    if errors:
        raise p.toolkit.ValidationError(errors)

    # Convert payload from CKAN to EC API spec

    ec_dict = custom_schema.convert_ckan_dataset_to_ec_dataset(
        validated_data_dict)

    # Send request to EC Data Collection API

    method, url = _get_api_endpoint('dataset_request_update')

    url = url.format(
        organization_id=validated_data_dict['owner_org'],
        dataset_id=validated_data_dict['id'],
    )

    headers = {
        'Authorization': _get_api_auth_token(),
        'Content-Type': 'application/json',
    }

    try:
        response = requests.request(method, url,
                                    data=json.dumps(ec_dict),
                                    headers=headers,
                                    )

        response.raise_for_status()
    except requests.exceptions.HTTPError:
        error_dict = {
            'message': ['The CTPEC API returned an error code'],
            'status': [response.status_code],
            'content': [response.content],
        }
        raise p.toolkit.ValidationError(error_dict)
    except requests.exceptions.RequestException, e:
        error_dict = {
            'message': ['Request exception: {0}'.format(e)],
        }
        raise p.toolkit.ValidationError(error_dict)

    try:
        content = response.json()
        request_id = content['RequestId']
    except ValueError:
        error_dict = {
            'message': ['Error decoding JSON from EC Platform response'],
            'content': [response.content],
        }
        raise p.toolkit.ValidationError(error_dict)
    except KeyError:
        error_dict = {
            'message': ['RequestId not in response from EC Platform'],
            'content': [response.content],
        }
        raise p.toolkit.ValidationError(error_dict)

    # Create a task status entry with the validated data
    # and store data in task status table

    task_dict = _create_task_status(context,
                                    task_type='dataset_request_update',
                                    # This will be used as dataset id
                                    entity_id=validated_data_dict['id'],
                                    entity_type='dataset',
                                    key='request_id',
                                    value=request_id,
                                    )

    # Return task id to access it later and the request id returned by the
    # EC Metadata API

    # _save_edit requires this key even though we have not actually created
    # a Package object. Model in context is horrible anyway.
    context['package'] = None

    return {
        'task_id': task_dict['id'],
        'request_id': request_id,
        # This is required by the core controller to do the redirect
        'name': validated_data_dict['name'],
    }


def resource_version_show(context, data_dict):
    '''Show files versions as listed on EC API'''
    try:
        resource_id = data_dict['resource_id']
        package_id = data_dict['package_id']
        #version_id = data_dict['version_id']
    except KeyError, e:
        raise p.toolkit.ValidationError(['No {0} provided'.format(e.msg)])

    resource = p.toolkit.get_action('resource_show')(context,
                                                     {'id': resource_id})
    #TODO: store ec_api_dataset_id in resource extra
    package_show = p.toolkit.get_action('package_show')
    dataset = package_show(context, {'name_or_id': package_id})

    method, url = _get_api_endpoint('file_version_show')

    try:
        ec_api_file_id = resource['ec_api_id'] 
    except KeyError, e:
        raise ECAPIValidationError(
            ['Error: {0} not in resource metadata'.format(e.message)])

    try:
        ec_api_org_id = dataset['ec_api_org_id']
        ec_api_dataset_id = dataset['ec_api_id']
    except KeyError, e:
        raise ECAPIValidationError(
            ['Error: {0} not in dataset metadata'.format(e.message)])

    url = url.format(
        organization_id=ec_api_org_id,
        dataset_id=ec_api_dataset_id,
        file_id=ec_api_file_id,
    )

    headers = {
        'Authorization': _get_api_auth_token(),
        'Content-Type': 'application/json',
    }

    response = requests.request(method, url, headers=headers)
    if response.status_code == requests.codes.ok:
        try:
            content = response.json()
        except ValueError:
            raise ECAPIValidationError(['EC API Error: response not JSON'])

    res_ec_to_ckan = custom_schema.convert_ec_file_to_ckan_resource
    try:
        metadata = content['MetadataResultSet']
    except IndexError:
        return {}

    versions = []
    if metadata:
        for version in metadata:
            ckan_resource = res_ec_to_ckan(version['FileMetadata'])
            ckan_resource['version'] = version['Version']
            versions.append(ckan_resource)
    return versions


def check_for_task_status_update(context, data_dict):
    '''Checks the EC Platform for updates and updates the TaskStatus'''
    # TODO check access
    try:
        task_id = data_dict['task_id']
    except KeyError:
        raise p.toolkit.ValidationError(['No task_id provided'])

    task_status = p.toolkit.get_action('task_status_show')(context,
        {'id': task_id})

    try:
        request_dict = json.loads(task_status.get('value', ''))
        method, url = _get_api_endpoint('request_status_show')
        url = url.format(request_id=request_dict['request_id'])
    except ValueError:
        raise p.toolkit.ValidationError(
            ['task_status value is not valid JSON'])
    except KeyError:
        raise p.toolkit.ValidationError(['no request_id in task_status value'])

    headers = {
        'Authorization': _get_api_auth_token(),
        'Content-Type': 'application/json',
    }

    response = requests.request(method, url, headers=headers)
    if response.status_code == requests.codes.ok:
        try:
            result = response.json()
        except ValueError:
            raise ECAPIValidationError(['EC API Error: response not JSON'])

        latest = result['Operations'][-1]
        latest_timestamp = dateutil.parser.parse(latest['Timestamp'],
                                                 yearfirst=True)

        task_status_timestamp = dateutil.parser.parse(
            task_status['last_updated'])


        if latest_timestamp > task_status_timestamp:
            if latest['OperationState'] == 'InProgress':

               task_status['state'] = 'in_progress'
               request_dict['ec_api_message'] = latest['Message']

            elif latest['OperationState'] == 'Failed':

               task_status['state'] = 'error'
               task_status['error'] = latest['Message']


            elif latest['OperationState'] == 'Succeeded':
                task_status['state'] = 'succeeded'
                request_dict['ec_api_message'] = latest['Message']

                # call dataset_create/user_create/etc
                try:
                    on_task_status_success(context, task_status)
                except NoSuchTaskType, e:
                    task_status['state'] = 'error'
                    # todo: fix abuse of task_status.value
                    request_dict['ec_api_message'] = e.message
                    
            task_status.update({
                'value': json.dumps(request_dict),
                'last_updated': latest['Timestamp'],
            })

            return  p.toolkit.get_action('task_status_update')(context,
                                                               task_status)
    else:
        raise ECAPIError('EC API returned an error: {0} - {1}'.format(
            response.status_code, url))


class NoSuchTaskType(Exception):
    pass


def on_task_status_success(context, task_status_dict):
    def on_dataset_request_create():
        request_dict = json.loads(task_status_dict['value'])
        ckan_data_dict = request_dict['data_dict']

        # TODO: the package should be owned by the user that created the
        #       request
        site_user = p.toolkit.get_action('get_site_user')(context, {})
        pkg_create_context = {
            'local_action': True,
            'user': site_user['name'],
            'model': model,
            'session': model.Session,
            'schema': custom_schema.ec_create_package_schema()
        }

        #todo update extras from successs

        #todo error handling
        p.toolkit.get_action('package_create')(pkg_create_context,
                                           ckan_data_dict)
        
    functions = {
        'dataset_request_create': on_dataset_request_create,
    }

    task_type = task_status_dict['task_type']
    try:
        functions[task_type]()
    except KeyError:
        raise NoSuchTaskType('no such task type {0}'.format(task_type))


@p.toolkit.side_effect_free
def get_change_request(context, data_dict):
    p.toolkit.check_access('get_change_request', context, data_dict)
    try:
        request_id = data_dict['id']
    except KeyError:
        raise p.toolkit.ValidationError(['id missing'])

    method, url = _get_api_endpoint('request_status_show')
    url = url.format(request_id=request_id)

    import ckanext.oauth2waad.plugin as oauth2waad_plugin
    try:
        access_token = oauth2waad_plugin.service_to_service_access_token()
        if not access_token.startswith('Bearer '):
            access_token = 'Bearer ' + access_token
        headers = {
            'Authorization': access_token,
            'Content-Type': 'application/json',
        }
    except oauth2waad_plugin.ServiceToServiceAccessTokenError, e:
        raise ECAPIError(['EC API Error: Failed to get service auth {0}'.format(e.message)])
    
    response = requests.request(method, url, headers=headers)
    if response.status_code == requests.codes.ok:
        try:
            results = response.json()
        except ValueError:
            raise ECAPIError(['EC API Error: could no decode response as JSON'])

        # change all the keys from CamelCase
        for result in results:
            for key in result.keys():
                key_underscore = re.sub('(?!^)([A-Z]+)', r'_\1', key).lower()
                result[key_underscore] = result.pop(key)

        return results

    else:
        raise ECAPIError(['EC API Error: {0} - {1}'.format(
            response.status_code, response.content)])


@p.toolkit.side_effect_free
def changelog_show(context, data_dict):
    '''
    Requests audit entries to the EC API Changelog API

    :param audit_id: The starting audit_id to return a set of changelog
                     records for. All records created since this audit_id
                     are returned (up until `top`)
                     If omitted then the single most recent changelog
                     record is returned.
    :type operation: int
    :param top: Number of records to return (defaults to 20)
    :type operation: int
    :param object_type: Limit records to this particular type (valid values
                        are `Dataset`, `File` or `Organisation`)
    :type operation: string

    :returns: a list with the returned audit objects
    :rtype: list
    '''

    p.toolkit.check_access('changelog_show', context, data_dict)

    audit_id = data_dict.get('audit_id')
    top = data_dict.get('top')
    object_type = data_dict.get('object_type')

    # Send request to EC Audit API

    method, url = _get_api_endpoint('changelog_show')

    if audit_id:
        url += '/{0}'.format(audit_id)

    params = {}
    if top:
        params['$top'] = top
    if object_type:
        params['$ObjectType'] = object_type

    # Get Service to Service auth token

    try:
        access_token = oauth2.service_to_service_access_token()
    except oauth2.ServiceToServiceAccessTokenError:
        log.warning('Could not get the Service to Service auth token')
        access_token = None

    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
        'Content-Type': 'application/json',
    }

    response = requests.request(method, url, headers=headers, params=params)

    content = response.json()

    # Check status codes

    status_code = response.status_code

    if status_code != 200:
        error_dict = {
            'message': ['The CTPEC API returned an error code'],
            'status': [status_code],
            'content': [content],
        }
        if status_code == 401:
            raise ECAPINotAuthorized(error_dict)
        else:
            raise p.toolkit.ValidationError(error_dict)

    return content
