import logging
import uuid
import urllib

from ckan import model
from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit

from ckanext.glasgow.logic.schema import (
    convert_ec_user_to_ckan_user,
    convert_ec_member_to_ckan_member,
    user_schema
)


log = logging.getLogger(__name__)

def create_user(ec_dict):
    data_dict = convert_ec_user_to_ckan_user(ec_dict)
    data_dict['password'] = str(uuid.uuid4())
    if not data_dict.get('email'):
        data_dict['email'] = 'noemail'


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
        'session': model.Session,
        'schema': user_schema(),
    }
    try:
        user = toolkit.get_action('user_create')(context, data_dict)
        if ec_dict.get('OrganisationId'):
            context = {
                'ignore_auth': True,
                'model': model,
                'user': site_user['name'],
                'session': model.Session,
                'local_action': True,
            }
            member_dict = convert_ec_member_to_ckan_member(ec_dict)
            try:
                toolkit.get_action('organization_show')(context, {'id': member_dict['id']})
                toolkit.get_action('organization_member_create')(context, member_dict)
            except toolkit.ObjectNotFound, e:
                log.warning('organization {} does not exist'.format(member_dict['id']))
        return user
    except toolkit.ValidationError, e:
        if e.error_dict.get('name') == [u'That login name is not available.']:
            log.debug('username exists skipping')
        else:
            raise e


def _create_users(ec_user_list):
    for ec_user in ec_user_list:
        user = create_user(ec_user)
        if user:
            log.debug('created user {0}'.format(user['id']))


class GetInitialUsers(CkanCommand):
    summary = "--NO SUMMARY--"
    usage = "--NO USAGE--"

    def command(self):
        self._load_config()
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
        ec_user_list = toolkit.get_action('ec_user_list')(context, {})
        _create_users(ec_user_list)
