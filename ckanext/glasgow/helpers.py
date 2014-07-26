import json
from ckan import model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckan.new_authz as new_authz

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


def is_user_an_admin_of_any_organization(user_name):
    '''Return True if the given user is an admin of any organization, or False.

    Always returns True for sysadmins.

    '''
    if new_authz.is_sysadmin(user_name):
        return True

    try:
        user_dict = toolkit.get_action('user_show')(
            context={}, data_dict={'id': user_name})
    except toolkit.ObjectNotFound:
        return False

    user_id = user_dict['id']

    q = model.Session.query(model.Member)
    q = q.filter(model.Member.state == 'active')
    q = q.filter(model.Member.table_name == 'user')
    q = q.filter(model.Member.capacity == 'admin')
    q = q.filter(model.Member.table_id == user_id)
    members = q.all()

    if [member for member in members if member.group.is_organization]:
        return True
    else:
        return False
