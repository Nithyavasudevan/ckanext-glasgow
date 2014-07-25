import ckan.plugins.toolkit as toolkit


class CreateUsersController(toolkit.BaseController):

    def create_users(self):
        return toolkit.render('create_users.html')
