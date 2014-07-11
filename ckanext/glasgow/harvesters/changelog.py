import logging
import json

import requests

from ckan import plugins as p
from ckan import model

from ckanext.harvest.model import HarvestObject

from ckanext.glasgow.logic.action import _get_api_endpoint
import ckanext.glasgow.logic.schema as custom_schema
from ckanext.glasgow.model import HarvestLastAudit
from ckanext.glasgow.harvesters import EcHarvester, get_dataset_name

log = logging.getLogger(__name__)


class EcChangelogHarvester(EcHarvester):

    force_import = False

    def info(self):
        return {
            'name': 'ec_changelog_harvester',
            'title': 'EC Changelog Harvester',
            'description': 'Harvester for regular Changelog imports from ' +
                           'the CTPEC API',

        }

    def gather_stage(self, harvest_job):
        log.debug('In ChangelogHarvester gather_stage')

        # Get the last harvested AuditId
        last_audit = model.Session.query(HarvestLastAudit) \
            .order_by(HarvestLastAudit.created.desc()) \
            .first()

        if last_audit:
            audit_id = last_audit.audit_id
        else:
            audit_id = '0'

        # Get all Audits
        audits = p.toolkit.get_action('changelog_show')(
            {'ignore_auth': True},
            {'audit_id': audit_id, 'top': 1000})

        # Check if there are any new audits to process
        if not len(audits) or (
           len(audits) == 1 and
           audits[0]['AuditId'] == audit_id):
            log.debug(
                'No new audits to process since last run ' +
                '(Last audit id {0})'.format(audit_id))
            return []

        # Ignore the first audit if an audit id was defined as start,
        # as this one will be included in the results
        audits = audits[1:] if audit_id != '0' and len(audits) > 1 else audits

        ids = []

        # TODO: Use the most recent update only
        for audit in audits:
            obj = HarvestObject(guid=audit['AuditId'], job=harvest_job,
                                content=json.dumps(audit))
            obj.save()
            ids.append(obj.id)

        # Save the last AuditId to know where to start in the next run
        new_last_audit = HarvestLastAudit(
            audit_id=audit['AuditId'],
            harvest_job_id=harvest_job.id,
        )
        new_last_audit.save()

        return ids

    def fetch_stage(self, harvest_object):
        return True

    def import_stage(self, harvest_object):

        audit = json.loads(harvest_object.content)

        command = audit.get('Command')

        handler = get_audit_command_handler(command)
        if not handler:
            log.warning(
                'No handler for command {0}, skipping ...'.format(command))
            return False

        context = {
            'ignore_auth': True,
            'user': self._get_user_name(),
            'local_action': True,
        }

        log.debug('Calling handler for command "{0}"'.format(command))
        try:
            handler(context, audit, harvest_object)
        except p.toolkit.ValidationError, e:
            self._save_object_error(str(e), harvest_object, 'Import')

        return True


def _get_latest_dataset_version(audit):

    method, url = _get_api_endpoint('dataset_show')

    url = url.format(
        organization_id=audit['CustomProperties'].get('OrganisationId'),
        dataset_id=audit['CustomProperties'].get('DataSetId'),
    )

    response = requests.request(method, url)

    if response.status_code != 200:
        return False

    content = response.json()
    dataset_dict = custom_schema.convert_ec_dataset_to_ckan_dataset(
        content['MetadataResultSet']['Metadata'])

    dataset_dict['owner_org'] = content['MetadataResultSet'].get(
        'OrganisationId')

    return dataset_dict


def handle_dataset_create(context, audit, harvest_object):

    dataset_dict = _get_latest_dataset_version(audit)

    if not dataset_dict.get('name'):
        dataset_dict['name'] = get_dataset_name(dataset_dict)

    new_dataset = p.toolkit.get_action('package_create')(context,
                                                         dataset_dict)

    log.debug('Created new dataset "{0}"'.format(new_dataset['id']))

    harvest_object.guid = new_dataset['id']  # Should be the same in the EC API
    harvest_object.package_id = new_dataset['id']
    harvest_object.current = True

    harvest_object.add()

    model.Session.commit()

    return True


def handle_dataset_update(context, audit, harvest_object):

    dataset_dict = _get_latest_dataset_version(audit)

    if not dataset_dict.get('name'):
        dataset_dict['name'] = get_dataset_name(dataset_dict)

    updated_dataset = p.toolkit.get_action('package_update')(context,
                                                             dataset_dict)

    log.debug('Created new dataset "{0}"'.format(updated_dataset['id']))

    harvest_object.guid = updated_dataset['id']  # Should be the same in the EC API
    harvest_object.package_id = updated_dataset['id']
    harvest_object.current = True

    harvest_object.add()

    previous_objects = model.Session.query(HarvestObject) \
        .filter(HarvestObject.guid==harvest_object.guid) \
        .filter(HarvestObject.current==True) \
        .all()

    for obj in previous_objects:
        obj.delete()

    model.Session.commit()

    return True


def get_audit_command_handler(command):

    handlers = {
        'CreateDataSet': handle_dataset_create,
        'UpdateDataset': handle_dataset_update,
    }

    return handlers.get(command)
