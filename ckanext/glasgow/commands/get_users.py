import logging
import uuid

from pylons import config

from ckan import model
from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit

from ckanext.glasgow.util import call_ec_api

log = logging.getLogger(__name__)

ckan_to_ec_user_mapping = {
    'name': 'UserId',
    'fullname': 'DisplayName',
}


def convert_ec_user_to_ckan_user(ec_dict):
    ''' Convert ec json to ckan data_dict

    This currently matches the way ckanext-oauth2waad maps users, we
    will need to keep this mapping consistent both here and in
    ckanext-oauth2waad
    '''
    ckan_dict = {}

    for ckan_name, ec_name in ckan_to_ec_user_mapping.iteritems():
        if ec_dict.get(ec_name):
            ckan_dict[ckan_name] = ec_dict.get(ec_name)

    ckan_dict.update({
        'password': str(uuid.uuid4()),
        'email': 'foo'
    })
    return ckan_dict


def create_user(ec_dict):
    data_dict = convert_ec_user_to_ckan_user(ec_dict)
    context = {
        'ignore_auth': True,
        'model': model,
        'session': model.Session
    }

    site_user = toolkit.get_action('get_site_user')(context, {})

    context = {
        'ignore_auth': True,
        'model': model,
        'user': site_user['name'],
        'session': model.Session
    }
    try:
        return toolkit.get_action('user_create')(context, data_dict)
    except toolkit.ValidationError, e:
        if e.error_dict.get('name') == [u'That login name is not available.']:
            log.debug('username exists skipping')
        else:
            raise e


class GetInitialUsers(CkanCommand):
    summary = "--NO SUMMARY--"
    usage = "--NO USAGE--"

    def command(self):
        self._load_config()
        api_url = config.get('ckanext.glasgow.identity_api', '').rstrip('/')
        api_endpoint = '{0}/Identity/User'.format(api_url)

        for ec_user in call_ec_api(api_endpoint):
            user = create_user(ec_user)
            log.debug('created user {0}'.format(user['id']))
