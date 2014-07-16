import json
from ckan import model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit

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
