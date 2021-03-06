import datetime
import json
from ckan import model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit

from ckanext.glasgow.logic.schema import resource_schema as custom_resource_schema
from ckanext.glasgow.logic.action import _get_api_endpoint
def get_licenses():

    return [('', '')] + model.Package.get_license_options()

def get_resource_versions(dataset_id, resource_id):
    try:
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
        }
        # we are provided revisions in ascending only by the EC API platform
        # but the requirement is for a descending list, so we are reversing it
        # here
        resource_versions_show = toolkit.get_action('resource_version_show')
        versions = resource_versions_show(context, {
            'package_id': dataset_id,
            'resource_id': resource_id,
        })
        if versions:
            versions.reverse()
        return versions
    except (toolkit.ValidationError, toolkit.NotAuthorized, toolkit.ObjectNotFound), e:

        helpers.flash_error('{0}'.format(e.error_dict['message']))
        return []

def get_pending_files_for_dataset(pkg_dict):
    try:
        pending_files = toolkit.get_action('pending_files_for_dataset')({
            'user': toolkit.c.user, }, {'name': pkg_dict['name']})
        for pending_file in pending_files:
            pending_file['value'] = json.loads(pending_file['value'])
        return pending_files

    except (toolkit.ValidationError,  toolkit.ObjectNotFound), e:
        helpers.flash_error('{0}'.format(e.error_dict['message']))
        return []
    except toolkit.NotAuthorized:
        return []


def get_pending_task_for_dataset(pkg_name):
    try:
        return toolkit.get_action('pending_task_for_dataset')({
            'user': toolkit.c.user, }, {'name': pkg_name})
    except (toolkit.ValidationError,  toolkit.ObjectNotFound), e:
        helpers.flash_error('{0}'.format(e.error_dict['message']))
        return None
    except toolkit.NotAuthorized:
        return None


def get_datetime_from_ec_iso(date_str):

    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        return date_str


def parse_metadata_string(metadata_str):
    return json.loads(metadata_str)


def get_resource_ec_extra_fields(resource_dict):

    if resource_dict.get('extras'):
        return resource_dict['extras']

    resource_schema_keys = custom_resource_schema().keys()
    resource_schema_keys.extend([
        'ec_api_org_id', 'FileName', 'DataSetId', 'can_be_previewed',
        'on_same_domain', 'clear_upload',
    ])

    extra_ec_fields = []
    for key, value in resource_dict.iteritems():
        if key not in resource_schema_keys:
            extra_ec_fields.append({'key': key, 'value': value})

    return extra_ec_fields


def get_ec_api_metadata_link(object_type, object_dict):

    url = None
    if object_type == 'organization':
        method, url = _get_api_endpoint('organization_show')
        url = url.format(
            organization_id=object_dict['id'],
        )
    elif object_type == 'dataset':
        method, url = _get_api_endpoint('dataset_show')
        url = url.format(
            organization_id=object_dict['owner_org'],
            dataset_id=object_dict['id']
        )

    return url
