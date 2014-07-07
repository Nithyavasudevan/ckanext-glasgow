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
