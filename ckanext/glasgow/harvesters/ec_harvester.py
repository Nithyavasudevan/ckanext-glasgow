import logging
import json

import dateutil.parser
from pylons import config
import requests
import slugify
from sqlalchemy.sql import update, bindparam

import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckanext.harvest.model import HarvestJob, HarvestObject, HarvestObjectExtra
from ckanext.harvest.harvesters.base import HarvesterBase

import ckanext.glasgow.logic.schema as glasgow_schema

log = logging.getLogger(__name__)


class EcHarvester(HarvesterBase):

    def _get_object_extra(self, harvest_object, key):
        '''
        Helper function for retrieving the value from a harvest object extra,
        given the key
        '''
        for extra in harvest_object.extras:
            if extra.key == key:
                return extra.value
        return None

    def _get_site_user(self):
        return toolkit.get_action('get_site_user')({
                'model': model,
                'session': model.Session,
                'ignore_auth': True,
                'defer_commit': True
            }, {})

    def _create_orgs(self, harvest_job):
        api_url = config.get('ckanext.glasgow.read_ec_api', '').rstrip('/')
        api_endpoint = '{0}/Metadata/Organisation'.format(api_url)

        request = requests.get(api_endpoint)
        if request.status_code != 200:
            self._save_gather_error('Unable to get content for URL: {0}:'.format(api_endpoint), harvest_job)
            return False

        result = json.loads(request.content)
        if result.get('IsErrorResponse', False):
            self._save_gather_error(
                'EC API Error: {0}:'.format(result.get('ErrorMessage', '')),
                harvest_job
            )
            return False

        orgs = result['MetadataResultSet']

        skip = 0


        # loop until there are do results, as we do not know the total
        # number of orgs.
        while orgs:
            for org in orgs:
                try:
                    # only create if the organization does not already exist
                    context = {
                        'model': model,
                        'session': model.Session,
                        'user': self._get_site_user()['name']
                    }
                    data_dict = {
                        'title': org['Title'],
                        'name': slugify.slugify(org['Title']),
                        'extras': [
                            {'key': 'ec_api_id', 'value': org['Id']},
                        ]
                    }
                    toolkit.get_action('organization_create')(context, data_dict)
                except toolkit.ValidationError, e:
                    pass

            skip += len(orgs)
            request = requests.get(api_endpoint, params={'$skip': skip})
            result = json.loads(request.content)

            orgs = result.get('MetadataResultSet', [])

        return toolkit.get_action('organization_list')(context, {})

    def _fetch_from_ec(self, harvest_job, request):

        if request.status_code != 200:
            self._save_gather_error(
                'Unable to get content for URL: {0}:'.format(request.url),
                harvest_job
            )
            return False

        result = json.loads(request.content)
        if result.get('IsErrorResponse', False):
            self._save_gather_error(
                'EC API Error: {0}:'.format(result.get('ErrorMessage', '')),
                harvest_job
            )
            return False
        return result

    def info(self):
        return {
            'name': 'ec_orgs',
            'title': 'EC Organization Harvester',
            'description': 'Harvester for EC Platform for Glasgow Project',

        }

    def gather_stage(self, harvest_job):
        previous_job = model.Session.query(HarvestJob) \
                        .filter(HarvestJob.source==harvest_job.source) \
                        .filter(HarvestJob.gather_finished!=None) \
                        .filter(HarvestJob.id!=harvest_job.id) \
                        .order_by(HarvestJob.gather_finished.desc()) \
                        .limit(1).first()

        orgs = self._create_orgs(harvest_job)
        if orgs is False:
            return False

        api_url = config.get('ckanext.glasgow.read_ec_api', '').rstrip('/')
        api_endpoint = api_url + '/Organisations/{0}/Datasets'

        context = {
            'model': model,
            'session': model.Session,
            'user': self._get_site_user()['name']
        }

        harvest_object_ids = []

        for org_name in orgs:
            org = toolkit.get_action('organization_show')(context,
                                                          {'id': org_name})
            values = [e['value'] for e in org.get('extras', []) if e['key'] == 'ec_api_id']
            if not len(values):
                log.warning('Could not get EC API id for organization {0}, skipping...'.format(org['name']))
                continue
            ec_api_org_id = values[0]

            endpoint = api_endpoint.format(ec_api_org_id)
            request = requests.get(endpoint)
            result = self._fetch_from_ec(harvest_job, request)
            if not result:
                return False

            datasets = result['MetadataResultSet']
            skip = 0
            while datasets:
                for dataset in datasets:
                    modified = dateutil.parser.parse(dataset.get('ModifiedTime'))

                    if not previous_job or not modified or modified > previous_job.gather_finished:
                        harvest_object = HarvestObject(
                            guid=dataset['Id'],
                            content=json.dumps(dataset),
                            job=harvest_job,
                            # Add reference to CKAN org to use on import stage
                            extras=[HarvestObjectExtra(key='owner_org', value=org['id'])]
                        )
                        harvest_object.save()
                        harvest_object_ids.append(harvest_object.id)

                skip += len(datasets)
                request = requests.get(
                    api_endpoint.format(org['id']),
                    params={'$skip': skip}
                )

                result = self._fetch_from_ec(harvest_job, request)
                if not result:
                    return False

                datasets = result.get('MetadataResultSet', [])

        return harvest_object_ids

    def fetch_stage(self, harvest_object):
        return True

    def import_stage(self, harvest_object):
        site_user = toolkit.get_action('get_site_user')({
                'model': model,
                'session': model.Session,
                'ignore_auth': True,
                'defer_commit': True
            }, {})

        context = {
            'model': model,
            'session': model.Session,
            'user': site_user['name'],
        }

        ec_data_dict = json.loads(harvest_object.content)
        ckan_data_dict = glasgow_schema.convert_ec_dataset_to_ckan_dataset(
            ec_data_dict.get('Metadata', {}))
        ckan_data_dict['__local_action'] = True

        # double check name
        if not ckan_data_dict.has_key('name'):
            ckan_data_dict['name'] = slugify.slugify(ec_data_dict['Title'])

        # Add EC APU ids
        ckan_data_dict['ec_api_org_id'] = ec_data_dict['OrganisationId']
        ckan_data_dict['ec_api_id'] = ec_data_dict['Id']

        try:
            owner_org = self._get_object_extra(harvest_object, 'owner_org')
            ckan_data_dict['owner_org'] = owner_org
            pkg = toolkit.get_action('package_create')(context,
                                                       ckan_data_dict)

            from ckanext.harvest.model import harvest_object_table
            conn = model.Session.connection()
            u = update(harvest_object_table) \
                    .where(harvest_object_table.c.package_id==bindparam('b_package_id')) \
                    .values(current=False)
            conn.execute(u, b_package_id=pkg['id'])

            harvest_object.package_id = pkg['id']
            harvest_object.current = True
            harvest_object.save()
        except toolkit.ValidationError, e:
            self._save_object_error('Invalid package with GUID %s: %r' % (harvest_object.guid, e.error_dict), harvest_object, 'Import')
            return False

        return True
