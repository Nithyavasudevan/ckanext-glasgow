import json

from pylons import config

import ckan.model as model
import ckan.lib.helpers as helpers
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
                change_requests = p.toolkit.get_action('get_change_request')(
                    context, {'id': pending_task['value'].get('request_id')})
                if change_requests:
                    change_request = change_requests[-1]
                else:
                    change_request = None
            except ECAPIError, e:
                change_request = None
                #flash
            except p.toolkit.NotAuthorized:
                change_request = None

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
            pkg = p.toolkit.get_action('package_show')(context, {'name_or_id': dataset})
        except p.toolkit.ObjectNotFound:
            return p.toolkit.abort(404, p.toolkit._('Package not found'))

        try:
            context = {
                'model': model,
                'session': model.Session,
                'user': p.toolkit.c.user,
            }
            # we are provided revisions in ascending only by the EC API platform
            # but the requirement is for a descending list, so we are reversing it
            # here
            resource_versions_show = p.toolkit.get_action('resource_version_show')
            versions = resource_versions_show(context, {
                'package_id': pkg['id'],
                'resource_id': resource,
            })
            if versions:
                versions.reverse()
            else:
               return p.toolkit.abort(404, 'no versions were found for this file')
        except p.toolkit.ValidationError, e:
            return p.toolkit.abort(404, 'error fetching versions: {0}'.format(str(e)))
        except p.toolkit.NotAuthorized, e:
            return p.toolkit.abort(401, 'error fetching versions: {0}'.format(str(e)))
        except p.toolkit.ObjectNotFound, e:
            return p.toolkit.abort(404, 'ObjectNotFound: error fetching versions: {0}'.format(str(e)))

        vars = {
            'pkg': pkg,
            'resource_id': resource,
            'version_id': int(version),
            'versions': versions
        }
        return p.toolkit.render('package/resource_versions.html',
                                extra_vars=vars)

    def resource_version_delete(self, dataset, resource, version=0):

        data_dict = {
            'id': resource
        }
        if version:
            data_dict['version_id'] = version

        p.toolkit.get_action('file_request_delete')({}, data_dict)

        helpers.flash_notice('Deletion of File version {0} was requested'.format(version))

        p.toolkit.redirect_to('resource_version')


    def dataset_change_requests(self, dataset_name):
        context = {
            'model': model,
            'session': model.Session,
        }
        try:
            pkg = p.toolkit.get_action('package_show')(context, {'name_or_id': dataset_name})
        except p.toolkit.ObjectNotFound:
            return p.toolkit.abort(404, p.toolkit._('Package not found'))

        try:
            task = p.toolkit.get_action('pending_task_for_dataset')(context,
                {'name': dataset_name, 'id': pkg['id']})
            if task:
                task['value'] = json.loads(task['value'])
                request_status = p.toolkit.get_action('get_change_request')(context,
                    {'id': task['value'].get('request_id')})
            else:
                request_status = None
        except p.toolkit.ValidationError, e:
            helpers.flash_error('{0}'.format(e.error_dict['message']))
        except ECAPIError:
            helpers.flash_error('{0}'.format(e.error_dict['message']))
        except p.toolkit.NotAuthorized:
            return p.toolkit.abort(401, p.toolkit._('Not authorized to view change requests'))


        return p.toolkit.render('package/change_request_list.html',
                                extra_vars={'pkg_dict': pkg,
                                            'change_request': request_status,
                                            'task': task,
                                            })

    def approvals(self):
        approvals_list = []
        try:
            approvals_list = p.toolkit.get_action('approvals_list')({}, {})
        except (ECAPINotAuthorized, p.toolkit.ValidationError), e:
            helpers.flash_error('The EC API returned and error: {0}'.format(str(e)))

        except p.toolkit.NotAuthorized:

            return p.toolkit.abort(401, p.toolkit._('Not authorized to view pending requests'))

        return p.toolkit.render('approvals.html',
                                extra_vars={'approvals': approvals_list})

    def approval_act(self, id, accept):

        accept = (accept == 'True')
        try:
            p.toolkit.get_action('approval_act')({}, {
                'request_id': id,
                'accept': accept})
        except p.toolkit.ValidationError, e:
            helpers.flash_error('The EC API returned and error: {0}'.format(str(e)))
        else:
            if accept:
                helpers.flash_success('Request {0} approved'.format(id))
            else:
                helpers.flash_error('Request {0} rejected'.format(id))

        p.toolkit.redirect_to('approvals_list')

    def approval_download(self, id):

        try:
            download = p.toolkit.get_action('approval_download')({}, {
                'request_id': id})
        except p.toolkit.ValidationError, e:
            helpers.flash_error('The EC API returned and error: {0}'.format(str(e)))

            p.toolkit.redirect_to('approvals_list')
        else:
            p.toolkit.response.headers = download['headers']
            return download['content']
