import json

from pylons import config

import ckan.model as model
from ckan.controllers.package import PackageController

import ckan.plugins as p

from ckanext.glasgow.logic.action import (
    ECAPINotAuthorized,
    ECAPIError,
)


class DatasetController(PackageController):

    def read(self, id, format='html'):

        pending_task = p.toolkit.get_action('pending_task_for_dataset')({
            'ignore_auth': True}, {'id': id})

        if (pending_task and
                pending_task['task_type'] == 'dataset_request_create'):
            pending_task['value'] = json.loads(pending_task['value'])

            context = {
                'model': model,
                'session': model.Session,
            }

            try:
                change_request = p.toolkit.get_action('get_change_request')(
                    context, {'id': pending_task['value'].get('request_id')})[-1]
            except ECAPIError, e:
                change_request = None
                #flash

            vars = {
                'task': pending_task,
                'change_request': change_request,
            }
            return p.toolkit.render('package/read_pending.html',
                                    extra_vars=vars)
        else:
            return super(DatasetController, self).read(id, format)

    def resource_read(self, dataset_id, resource_id):
        pending_task = p.toolkit.get_action('pending_task_for_file')({
            'ignore_auth': True}, {'id': id})

        if (pending_task and
                pending_task['task_type'] == 'file_request_create'):
            pending_task['value'] = json.loads(pending_task['value'])

            context = {
                'model': model,
                'session': model.Session,
            }

            try:
                change_request = p.toolkit.get_action('get_change_request')(
                    context, {'id': pending_task['value'].get('request_id')})[-1]
            except ECAPIError, e:
                change_request = None

            vars = {
                'task': pending_task,
                'change_request': change_request,
            }
            return p.toolkit.render('package/resource_read_pending.html',
                                    extra_vars=vars)
        else:
            return super(DatasetController, self).resource_read(
                dataset_id, resource_id)

    def new(self, data=None, errors=None, error_summary=None):
        '''Needed to capture custom exceptions'''
        return super(DatasetController, self).new(data, errors,
                                                  error_summary)

    def _save_new(self, context, package_type=None):
        try:
            return super(DatasetController, self)._save_new(context,
                                                            package_type)
        except ECAPINotAuthorized, e:
            vars = {'error_type': 'auth'}
            return p.toolkit.render('package/read_api_error.html',
                                    extra_vars=vars)

    def new_resource(self, id, data=None, errors=None, error_summary=None):
        try:
            return super(DatasetController, self).new_resource(id, data,
                                                               errors,
                                                               error_summary)
        except ECAPINotAuthorized, e:
            vars = {'error_type': 'auth'}
            return p.toolkit.render('package/read_api_error.html',
                                    extra_vars=vars)

    def auth_token(self):

        if p.toolkit.request.method == 'GET':

            return p.toolkit.render('auth_token.html')

        elif p.toolkit.request.method == 'POST':
            token = p.toolkit.request.POST.get('token')
            if not token:
                vars = {'error': 'Please enter a value'}
                return p.toolkit.render('auth_token.html', extra_vars=vars)

            tmp_token_file = config.get('ckanext.glasgow.tmp_auth_token_file')
            try:
                with open(tmp_token_file, 'w') as f:
                    token = token.strip()
                    if not token.startswith('Bearer '):
                        token = 'Bearer ' + token
                    f.write(token)
                    vars = {'msg': 'Authorization token updated'}
                    return p.toolkit.render('auth_token.html', extra_vars=vars)

            except IOError:
                error = ('Could not write to temp auth token file: {0}'
                         .format(tmp_token_file))
                log.critical(error)
                vars = {'error': error}
                return p.toolkit.render('auth_token.html', extra_vars=vars)

    def resource_version(self, dataset, resource, version=0):
        context = {
            'model': model,
            'session': model.Session,
        }
        try:
            pkg =p.toolkit.get_action('package_show')(context, {'name_or_id': dataset})
        except p.toolkit.ObjectNotFound:
            return p.toolkit.abort(404, p.toolkit._('Package not found'))

        vars = {
            'pkg': pkg,
            'resource_id': resource,
            'version_id': int(version),
        }
        return p.toolkit.render('package/resource_versions.html',
                                extra_vars=vars)
