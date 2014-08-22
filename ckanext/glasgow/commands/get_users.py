import logging
import uuid
import urllib

from pylons import config
import requests

from ckan import model
from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit

from ckanext.glasgow.logic.schema import (
    convert_ec_user_to_ckan_user,
    convert_ec_member_to_ckan_member,
    user_schema
)

from ckanext.glasgow.harvesters import get_org_name
from ckanext.glasgow.harvesters.ec_harvester import _fetch_from_ec


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
        is_admin = [ i for i in ec_dict.get('Roles', []) if i == 'SuperAdmin']
        if is_admin:
            data_dict['sysadmin'] = True

        user = toolkit.get_action('user_create')(context, data_dict)
        if ec_dict.get('OrganisationId') and not is_admin:
            context = {
                'ignore_auth': True,
                'model': model,
                'user': site_user['name'],
                'session': model.Session,
                'local_action': True,
            }
            member_dict = convert_ec_member_to_ckan_member(ec_dict)
            try:
                org = toolkit.get_action('organization_show')(context, {'id': member_dict['id']})
            except toolkit.ObjectNotFound, e:
                org = create_orgs(site_user['name'])
            if org:
                toolkit.get_action('organization_member_create')(context, member_dict)

        return user
    except toolkit.ValidationError, e:
        if e.error_dict.get('name') == [u'That login name is not available.']:
            print 'username exists skipping'
        else:
            raise e


def create_orgs(organization_id, site_user):
    api_url = config.get('ckanext.glasgow.metadata_api', '').rstrip('/')
    api_endpoint = '{}/Metadata/Organisation/{}'.format(api_url, organization_id)

    request = requests.get(api_endpoint, verify=False)
    try:
        org = _fetch_from_ec(request)['MetaDataResultSet']
    except KeyError:
        print 'failed to fetch org {} from EC'.format(organization_id)
        return

    context = {
        'model': model,
        'session': model.Session,
        'user': site_user,
        'local_action': True,
    }
    org_name = get_org_name(org, 'Title')
    data_dict = {
        'id': org['Id'],
        'title': org['Title'],
        'name': org_name,
    }

    try:
        toolkit.get_action('organization_create')(context, data_dict)
        return toolkit.get_action('organization_show')(context, {id: organization_id})
    except toolkit.ValidationError:
        print 'failed to create org {}'.format(organization_id)


def _create_users(ec_user_list):
    for ec_user in ec_user_list:
        user = create_user(ec_user)
        if user:
            print 'created user {0}'.format(user['id'])


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
        u
        ec_user_list = toolkit.get_action('ec_user_list')(context, {})
        _create_users(ec_user_list)
