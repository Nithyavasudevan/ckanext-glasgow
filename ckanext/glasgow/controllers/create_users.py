import ckan.model as model
import ckan.new_authz as new_authz
import ckan.plugins.toolkit as toolkit


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
        user = toolkit.c.user
        is_sysadmin = new_authz.is_sysadmin(user)

        if is_sysadmin:
            organisation_names = toolkit.get_action('organization_list')(
                context={}, data_dict={})
        else:
            organisation_names = organizations_that_user_is_admin_of(user)

        return toolkit.render(
            'create_users.html',
            extra_vars={'organisation_names': organisation_names,
                        'is_sysadmin': is_sysadmin})
