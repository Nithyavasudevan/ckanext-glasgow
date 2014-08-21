from nose.tools import (
    assert_dict_contains_subset
)


import ckan.new_tests.helpers as helpers

from ckanext.glasgow.commands.get_users import create_user

class TestOrganizationUpdate(object):
    def setup(self):
        self.ec_dict = {
            u'About': u'Description',
            u'DisplayName': u'John Doe',
            u'Email': u'john.doe@org.com',
            u'FirstName': u'John',
            u'IsRegistered': False,
            u'LastName': u'Doe',
            u'OrganisationId': u'de0f2f6e-58ca-4a7b-95b1-7fd6e8df1f69',
            u'Roles': [u'OrganisationEditor'],
            u'UserId': u'dcfb1b12-fe52-4d71-9aad-c60fc4c6952c',
            u'UserName': u'johndoe'
        }
        self.org_owner = helpers.call_action('user_create',
                                               name='org_owner',
                                               email='test@test.com',
                                               password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'org_owner',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       id=u'de0f2f6e-58ca-4a7b-95b1-7fd6e8df1f69')


    def teardown(self):
        helpers.reset_db()

    def test_creates_users(self):
        user = create_user(self.ec_dict)
        assert_dict_contains_subset({
                 'id': u'dcfb1b12-fe52-4d71-9aad-c60fc4c6952c',
                 'name': u'johndoe',
                 'fullname': u'John Doe',
                 'about': u'Description',
                 'email': u'john.doe@org.com',
            },
            user
        )

    def test_user_already_exists_does_not_fail_validation_error(self):
        create_user(self.ec_dict)
        create_user(self.ec_dict)


class TestCreateUserWithNoEmail(object):
    def setup(self):
        self.ec_dict = {
            u'About': u'Description',
            u'DisplayName': u'',
            u'Email': u'',
            u'FirstName': u'',
            u'IsRegistered': False,
            u'LastName': u'',
            u'OrganisationId': u'de0f2f6e-58ca-4a7b-95b1-7fd6e8df1f69',
            u'Roles': [u'OrganisationEditor'],
            u'UserId': u'dcfb1b12-fe52-4d71-9aad-c60fc4c6952c',
            u'UserName': u'johndoe'
        }
        self.org_owner = helpers.call_action('user_create',
                                               name='org_owner',
                                               email='test@test.com',
                                               password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'org_owner',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       id=u'de0f2f6e-58ca-4a7b-95b1-7fd6e8df1f69')


    def teardown(self):
        helpers.reset_db()

    def test_creates_user_no_email(self):
        user = create_user(self.ec_dict)
        assert_dict_contains_subset({
                 'id': u'dcfb1b12-fe52-4d71-9aad-c60fc4c6952c',
                 'name': u'johndoe',
                 'about': u'Description',
                 'email': u'noemail',
            },
            user
        )

    def test_user_already_exists_does_not_fail_validation_error(self):
        create_user(self.ec_dict)
        create_user(self.ec_dict)


class TestCreateUserWithNoEmail(object):
    def setup(self):
        self.ec_dict = {
            "UserName": "741c5e3e-53d0-431e-9f10-b6ebd39590f4",
            "About": "",
            "DisplayName": "",
            "Roles": [
                "ExternalService"
                ],
            "FirstName": "",
            "LastName": "",
            "UserId": "e350cb61-ed72-4335-b915-7617b5e931f0",
            "IsRegistered": False,
            "OrganisationId": None,
            "Email": ""

            }
        self.org_owner = helpers.call_action('user_create',
                                               name='org_owner',
                                               email='test@test.com',
                                               password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'org_owner',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       id=u'de0f2f6e-58ca-4a7b-95b1-7fd6e8df1f69')


    def teardown(self):
        helpers.reset_db()

    def test_creates_user_no_email(self):
        user = create_user(self.ec_dict)
        assert_dict_contains_subset({
                 'id': u'e350cb61-ed72-4335-b915-7617b5e931f0',
                 'name': u'741c5e3e-53d0-431e-9f10-b6ebd39590f4',
                 'email': u'noemail',
            },
            user
        )

    def test_user_already_exists_does_not_fail_validation_error(self):
        create_user(self.ec_dict)
        create_user(self.ec_dict)
        

class TestCreateUserNameIsEmail(object):
    def setup(self):

        self.ec_dict = {

            "UserName": "EditorGCC1@GCCCTPECADINT.onmicrosoft.com",
            "About": "",
            "DisplayName": "",
            "Roles": [
                "OrganisationEditor"
                ],
            "FirstName": "",
            "LastName": "",
            "UserId": "e350cb61-ed72-4335-b915-7617b5e931f0",
            "IsRegistered": False,
            "OrganisationId": "f8c84440-24c6-40ce-a0b0-eafacd15ac59",
            "Email": ""

            }
        self.org_owner = helpers.call_action('user_create',
                                               name='org_owner',
                                               email='test@test.com',
                                               password='test')

        self.test_org = helpers.call_action('organization_create',
                                       context={
                                           'user': 'org_owner',
                                           'local_action': True,
                                       },
                                       name='test_org',
                                       id=u'f8c84440-24c6-40ce-a0b0-eafacd15ac59')


    def teardown(self):
        helpers.reset_db()

    def test_creates_user_no_email(self):
        user = create_user(self.ec_dict)
        assert_dict_contains_subset({
                 'id': u'e350cb61-ed72-4335-b915-7617b5e931f0',
                 'name': 'EditorGCC1@GCCCTPECADINT.onmicrosoft.com',
                 'email': u'noemail',
            },
            user
        )

    def test_user_already_exists_does_not_fail_validation_error(self):
        create_user(self.ec_dict)
        create_user(self.ec_dict)
