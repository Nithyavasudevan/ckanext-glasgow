import pylons

import ckan.model as model
import ckan.new_authz as new_authz
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers

from ckanext.glasgow.logic.action import ECAPINotFound

class CreateUsersController(toolkit.BaseController):
    def create_users(self):

        # extra_vars has to contain 'data' or the template will crash.
        # Replace data with a non-empty dict to pre-fill the form fields.
        extra_vars = {'data': {}}

        if toolkit.request.method == 'POST':
            params = dict(toolkit.request.params)
            try:
                if params['organisation']:
                    organisation_id = toolkit.get_action('organization_show')(
                        context={}, data_dict={'id': params['organisation']})['id']
            except toolkit.ObjectNotFound:
                helpers.flash_error('Organization {} not found'.format(
                    params['organisation']))
                return toolkit.render('create_users/create_users.html', extra_vars=extra_vars)

            confirm = params.pop('confirm-password')
            if confirm != params['Password']:
                helpers.flash_error('passwords do not match')
                return toolkit.render('create_users/create_users.html', extra_vars=extra_vars)

            context = {'model': model, 'session': model.Session}
            data_dict = {
                'UserName': params['Username'],
                'Password': params['Password'],
                'IsRegisteredUser': True,
                'Email': params['Email'],
                'FirstName': params['First Name'],
                'LastName': params['Last Name'],
                'DisplayName': params['Display Name'],
                'About': params['About'],
                'OrganisationId': params.get('organisation'),
            }
            try:
                request = toolkit.get_action('ec_user_create')(context, data_dict)
            except ECAPINotFound, e:
                helpers.flash_error('Error CTPEC platform returned an error: {}'.format(str(e)))
                return toolkit.render('create_users/create_users.html', extra_vars=extra_vars)
            except toolkit.ValidationError, e:
                helpers.flash_error('Error validating fields {}'.format(str(e)))
                return toolkit.render('create_users/create_users.html', extra_vars=extra_vars)
            helpers.flash_success('A request to create user {} was sent, your request id is {}'.format(params['Username'], request['request_id']))

        user = toolkit.c.user
        extra_vars['is_sysadmin'] = new_authz.is_sysadmin(user)

        if extra_vars['is_sysadmin']:
            extra_vars['organisation_names'] = toolkit.get_action(
                'organization_list')(context={}, data_dict={})
        else:
            context = {
                'model': model,
                'session': model.Session,
                'user': toolkit.c.user,
            }
            orgs = toolkit.get_action('organization_list_for_user')(context, {})
            extra_vars['organisation_names'] = ([o['name'] for o in orgs])

        return toolkit.render('create_users/create_users.html', extra_vars=extra_vars)
