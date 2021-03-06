import logging
import json
import hashlib
import datetime
import uuid

import requests

from ckan import plugins as p
from ckan import model

from ckanext.harvest.model import HarvestObject

from ckanext.glasgow.logic.action import _get_api_endpoint, _expire_task_status

import ckanext.glasgow.logic.schema as custom_schema
from ckanext.glasgow.model import HarvestLastAudit
from ckanext.glasgow.harvesters import (
    EcHarvester,
    get_dataset_name_from_task,
    get_initial_dataset_name,
    get_task_for_request_id,
    get_org_name,
)


log = logging.getLogger(__name__)


def save_last_audit_id(audit_id, harvest_job_id=None):

    new_last_audit = HarvestLastAudit(
        audit_id=audit_id,
        harvest_job_id=harvest_job_id,
    )
    new_last_audit.save()


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
        update_audits = {}
        for audit in audits:
            # We only want to use the most recent update per object per run
            # Store the most recent audit against a hash of the id fields
            if 'update' in audit['Command'].lower():
                m = hashlib.md5()
                m.update(json.dumps(audit['CustomProperties']))
                ids_hash = m.hexdigest()
                update_audits[ids_hash] = audit
            else:
                obj = HarvestObject(guid=audit['AuditId'], job=harvest_job,
                                    content=json.dumps(audit))
                obj.save()
                ids.append(obj.id)

        # Save the last AuditId to know where to start in the next run
        save_last_audit_id(audit['AuditId'], harvest_job.id)

        for key, audit in update_audits.iteritems():
            obj = HarvestObject(guid=audit['AuditId'], job=harvest_job,
                                content=json.dumps(audit))
            obj.save()
            ids.append(obj.id)

        return ids

    def fetch_stage(self, harvest_object):
        return True

    def import_stage(self, harvest_object):

        audit = json.loads(harvest_object.content)

        log.debug('Import stage for audit "{0}"'.format(audit.get('AuditId')))

        command = audit.get('Command')

        handler = get_audit_command_handler(command)
        if not handler:
            log.warning(
                'No handler for command {0}, skipping ...'.format(command))
            return False

        context = {
            'model': model,
            'ignore_auth': True,
            'user': self._get_user_name(),
            'local_action': True,
        }

        log.debug('Calling handler for command "{0}"'.format(command))
        try:

            request_id = audit.get('RequestId')

            # Mark relevant task as in progress
            self._mark_task_as_processing(context, request_id)

            handler(context, audit, harvest_object)

            self._mark_task_as_finished(context, request_id)

            return True
        except p.toolkit.ValidationError, e:
            self._save_object_error(str(e), harvest_object, 'Import')
        except p.toolkit.ObjectNotFound, e:
            msg = e.message or str(e) or 'Object not found'
            self._save_object_error(msg, harvest_object, 'Import')

        return False

    def _mark_task_as_processing(self, context, request_id):
        return self._update_task_state(context, request_id, 'processing')

    def _mark_task_as_finished(self, context, request_id):
        return self._update_task_state(context, request_id, 'finished')

    def _update_task_state(self, context, request_id, state):

        task = get_task_for_request_id(context, request_id)

        if task:
            task.state = state
            task.last_updated = datetime.datetime.now()

            task.save()

            _expire_task_status(context, task.id)

            return True

        return False


def _get_latest_organization_version(audit):

    method, url = _get_api_endpoint('organization_show')

    url = url.format(
        organization_id=audit['CustomProperties'].get('OrganisationId'),
    )

    response = requests.request(method, url, verify=False)

    if response.status_code != 200:
        return False

    content = response.json()

    if not content.get('MetadataResultSet'):
        return False

    org_dict = custom_schema.convert_ec_organization_to_ckan_organization(
        content['MetadataResultSet'][0])

    org_dict['id'] = str(content['MetadataResultSet'][0]['Id'])

    return org_dict


def _get_latest_dataset_version(audit):

    method, url = _get_api_endpoint('dataset_show')

    url = url.format(
        organization_id=audit['CustomProperties'].get('OrganisationId'),
        dataset_id=audit['CustomProperties'].get('DataSetId'),
    )

    response = requests.request(method, url, verify=False)

    if response.status_code != 200:
        return False

    content = response.json()

    if not content.get('MetadataResultSet'):
        return False

    dataset_dict = custom_schema.convert_ec_dataset_to_ckan_dataset(
        content['MetadataResultSet']['Metadata'])

    dataset_dict['id'] = str(content['MetadataResultSet']['Id'])

    dataset_dict['owner_org'] = content['MetadataResultSet'].get(
        'OrganisationId')

    dataset_dict['needs_approval'] = content['MetadataResultSet'].get(
        'NeedsApproval')

    return dataset_dict


def _get_file_version(audit):

    # Starting from iteration 4 all Files have a VersionId

    method, url = _get_api_endpoint('file_version_show')
    url = url.format(
        organization_id=audit['CustomProperties'].get('OrganisationId'),
        dataset_id=audit['CustomProperties'].get('DataSetId'),
        file_id=audit['CustomProperties'].get('FileId'),
        version_id=audit['CustomProperties'].get('VersionId'),
    )

    response = requests.request(method, url, verify=False)

    if response.status_code != 200:
        return False

    content = response.json()

    if not content.get('MetadataResultSet'):
        return False

    resource_dict = custom_schema.convert_ec_file_to_ckan_resource(
        content['MetadataResultSet']['FileMetadata'])

    resource_dict['id'] = str(content['MetadataResultSet']['FileId'])

    resource_dict['package_id'] = str(content['MetadataResultSet'].get(
        'DataSetId'))

    resource_dict['ec_api_org_id'] = content['MetadataResultSet'].get(
        'OrganisationId')

    resource_dict['ec_api_version_id'] = content['MetadataResultSet'].get(
        'Version')

    return resource_dict


def handle_dataset_create(context, audit, harvest_object):

    dataset_dict = _get_latest_dataset_version(audit)

    if not dataset_dict:
        msg = ['Could not get remote dataset metadata: {0}'.format(
            json.dumps(audit['CustomProperties']))]
        raise p.toolkit.ObjectNotFound(msg)

    if not dataset_dict.get('name'):
        name = get_dataset_name_from_task(context, audit)
        if not name:
            name = get_initial_dataset_name(dataset_dict)
        dataset_dict['name'] = name

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

    if not dataset_dict:
        msg = ['Could not get remote dataset metadata: {0}'.format(
            json.dumps(audit['CustomProperties']))]
        raise p.toolkit.ObjectNotFound(msg)

    if not dataset_dict.get('name'):
        name = get_dataset_name_from_task(context, audit)
        if not name:
            name = get_initial_dataset_name(dataset_dict)
        dataset_dict['name'] = name

    updated_dataset = p.toolkit.get_action('package_update')(context,
                                                             dataset_dict)

    log.debug('Updated dataset "{0}"'.format(updated_dataset['id']))

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


def handle_file_create(context, audit, harvest_object):

    resource_dict = _get_file_version(audit)

    dataset_id = audit['CustomProperties'].get('DataSetId')

    if not resource_dict:
        msg = ['Could not get remote file metadata: {0}'.format(
            json.dumps(audit['CustomProperties']))]
        raise p.toolkit.ObjectNotFound(msg)

    try:
        p.toolkit.get_action('resource_show')(context,
                                              {'id': resource_dict['id']})
        is_version = True
        log.debug('Resource "{0}" exists, updating it ...'.format(resource_dict['id']))
    except p.toolkit.ObjectNotFound, e:
        is_version = False
        log.debug('Resource "{0}" does not exist, creating it ...'.format(resource_dict['id']))

    if is_version:
        resource_dict = p.toolkit.get_action('resource_update')(context,
                                                                resource_dict)
        log.debug('Updated existing resource "{0}" on dataset {1}'.format(
                  resource_dict['id'], dataset_id))
    else:
        try:
            resource_dict = p.toolkit.get_action('resource_create')(context,
                                                                    resource_dict)

            log.debug('Created new resource "{0}" on dataset {1}'.format(
                      resource_dict['id'], dataset_id))

        except p.toolkit.ObjectNotFound, e:
            e.extra_msg = ['Could not create resource, parent dataset {0} not found'.format(
                dataset_id)]
            raise e

    harvest_object.guid = dataset_id
    harvest_object.package_id = dataset_id
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


def handle_file_delete(context, audit, harvest_object):

    resource_id = audit['CustomProperties'].get('FileId')
    dataset_id = audit['CustomProperties'].get('DataSetId')

    try:
        p.toolkit.get_action('resource_delete')(context,
                                                {'id': resource_id})
    except p.toolkit.ObjectNotFound:
        log.debug('Resource "{0}" does not exist, it can not be deleted'.format(resource_id))

    log.debug('Deleted existing resource "{0}"'.format(resource_id))

    harvest_object.guid = dataset_id
    harvest_object.package_id = dataset_id
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


def handle_file_update(context, audit, harvest_object):

    resource_dict = _get_file_version(audit)

    dataset_id = audit['CustomProperties'].get('DataSetId')

    if not resource_dict:
        msg = ['Could not get remote file metadata: {0}'.format(
            json.dumps(audit['CustomProperties']))]
        raise p.toolkit.ObjectNotFound(msg)

    try:
        p.toolkit.get_action('resource_show')(context,
                                              {'id': resource_dict['id']})
        log.debug('Resource "{0}" exists, updating it ...'.format(resource_dict['id']))
    except p.toolkit.ObjectNotFound, e:
        e.extra_msg = ['Could not find resource {0}'.format(resource_dict['id'])]
        raise e

    resource_dict = p.toolkit.get_action('resource_update')(context,
                                                            resource_dict)
    log.debug('Updated existing resource "{0}" on dataset {1}'.format(
              resource_dict['id'], dataset_id))

    harvest_object.guid = dataset_id
    harvest_object.package_id = dataset_id
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


def handle_organization_create(context, audit, harvest_object):

    org_dict = _get_latest_organization_version(audit)

    if not org_dict:
        msg = ['Could not get remote organization metadata: {0}'.format(
            json.dumps(audit['CustomProperties']))]
        raise p.toolkit.ObjectNotFound(msg)

    if not org_dict.get('name'):
        name = get_dataset_name_from_task(context, audit)
        if not name:
            name = get_org_name(org_dict, 'title')
        org_dict['name'] = name

    new_org = p.toolkit.get_action('organization_create')(context,
                                                          org_dict)

    log.debug('Created new organization "{0}"'.format(new_org['id']))

    return True


def handle_organization_update(context, audit, harvest_object):

    org_dict = _get_latest_organization_version(audit)

    if not org_dict:
        msg = ['Could not get remote organization metadata: {0}'.format(
            json.dumps(audit['CustomProperties']))]
        raise p.toolkit.ObjectNotFound(msg)

    if not org_dict.get('name'):
        name = get_dataset_name_from_task(context, audit)
        if not name:
            name = get_org_name(org_dict, 'title')
        org_dict['name'] = name

    new_org = p.toolkit.get_action('organization_update')(context,
                                                          org_dict)

    log.debug('Updated organization "{0}"'.format(new_org['id']))

    return True


def handle_user_create(context, audit, harvest_object):
    username = audit['CustomProperties']['UserName']

    user = p.toolkit.get_action('ec_user_show')(
        context, {'ec_username': username})
    user_dict = custom_schema.convert_ec_user_to_ckan_user(user)
    user_dict['password'] = str(uuid.uuid4())

    new_user = p.toolkit.get_action('user_create')(context, user_dict)

    membership = custom_schema.convert_ec_member_to_ckan_member(user)
    p.toolkit.get_action('organization_member_create')(
        context, membership)
    log.debug('Created new user "{}" in org {}'.format(new_user['name'],
                                                       membership['id']))

    return True


def handle_user_update(context, audit, harvest_object):
    username = audit['CustomProperties']['UserName']

    user = p.toolkit.get_action('ec_user_show')(
        context, {'ec_username': username})
    user_dict = custom_schema.convert_ec_user_to_ckan_user(user)

    ckan_user = p.toolkit.get_action('user_update')(context, user_dict)

    current_memberships = p.toolkit.get_action('organization_list_for_user')(
        context, {'user': ckan_user['name'], 'permission': 'create_dataset'})

    # remove the user from all orgs
    for membership in current_memberships:
        p.toolkit.get_action('organization_member_delete')(context,
            {'id': membership['id'], 'username': ckan_user['name']})

    # add them to the org from ec
    membership = custom_schema.convert_ec_member_to_ckan_member(user)
    p.toolkit.get_action('organization_member_create')(
        context, membership)

    log.debug('Updated user "{}" in org {}'.format(ckan_user['name'],
                                                   membership['id']))

    return True


def get_audit_command_handler(command):

    handlers = {
        'CreateDataSet': handle_dataset_create,
        'UpdateDataSet': handle_dataset_update,
        'CreateFile': handle_file_create,
        'UpdateFile': handle_file_update,
        'DeleteFileVersion': handle_file_delete,
        'CreateOrganisation': handle_organization_create,
        'UpdateOrganisation': handle_organization_update,
        'CreateUser': handle_user_create,
        'UpdateUser': handle_user_update,
        'ChangeUserRoles': handle_user_update,
    }

    return handlers.get(command)
