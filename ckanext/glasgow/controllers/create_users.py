import ckan.plugins.toolkit as toolkit


class CreateUsersController(toolkit.BaseController):

    def create_users(self):

        # Get the list of organisations that the logged-in user is an admin
        # of.
        # FIXME: This is just getting all organisations!
        organisation_names = toolkit.get_action('organization_list')(
            context=None, data_dict={})

        return toolkit.render(
            'create_users.html',
            extra_vars={'organisation_names': organisation_names})
