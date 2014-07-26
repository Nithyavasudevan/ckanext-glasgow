import pylons
import requests
import json

import ckan.model as model
import ckan.new_authz as new_authz
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers


def organizations_that_user_is_admin_of(user):
    '''Return the list of organizations that the given user is an admin of.

    :param user: the name of the user
    :type user: string

    :returns: a list of organization names
    :rtype: list of strings

    '''
    user_dict = toolkit.get_action('user_show')(context={},
                                                data_dict={'id': user})
    user_id = user_dict['id']

    q = model.Session.query(model.Member)
    q = q.filter(model.Member.state == 'active')
    q = q.filter(model.Member.table_name == 'user')
    q = q.filter(model.Member.capacity == 'admin')
    q = q.filter(model.Member.table_id == user_id)
    members = q.all()

    group_names = [member.group.name for member in members
                   if member.group.is_organization]

    return group_names


class CreateUsersController(toolkit.BaseController):

    def create_users(self):

        # extra_vars has to contain 'data' or the template will crash.
        # Replace data with a non-empty dict to pre-fill the form fields.
        extra_vars = {'data': {}}

        if toolkit.request.method == 'POST':

            params = dict(toolkit.request.params)

            organisation = params.pop('organisation')
            organisation_id = toolkit.get_action('organization_show')(
                context={}, data_dict={'id': organisation})['id']

            # Get the URL to post to from the config file.
            url = pylons.config.get('ckanext.glasgow.metadata_api')
            if not url.endswith('/'):
                url = url + '/'
            url = url + 'Identity/Organisation/{organisation}/User'
            url = url.format(organisation=organisation_id)

            # TODO: Verify that passwords match.
            del params['confirm-password']

            # TODO: We could validate the params here, and re-render the form
            # with errors if any fail to validate.

            access_token = pylons.session.get(
                'ckanext-oauth2waad-access-token')

            try:
                response = requests.post(
                    url, data=json.dumps(params),
                    headers={'Authorization': access_token})
            except requests.ConnectionError as err:
                helpers.flash_error(str(err))
                extra_vars['data'] = dict(toolkit.request.params)

            if response.status_code == 200:
                helpers.flash_success('A request to create user {username} '
                    'was successfully sent to The Platform.'.format(
                    username=params['Username']))
            else:
                helpers.flash_error('The Platform returned an error: '
                    '{status} {reason}'.format(
                    status=str(response.status_code), reason=response.reason))
                extra_vars['data'] = dict(toolkit.request.params)

        user = toolkit.c.user
        extra_vars['is_sysadmin'] = new_authz.is_sysadmin(user)

        if extra_vars['is_sysadmin']:
            extra_vars['organisation_names'] = toolkit.get_action(
                'organization_list')(context={}, data_dict={})
        else:
            extra_vars['organisation_names'] = (
                organizations_that_user_is_admin_of(user))

        return toolkit.render('create_users.html', extra_vars=extra_vars)
