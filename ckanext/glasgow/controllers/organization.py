import json

from pylons import tmpl_context as c

from ckan.controllers.organization import OrganizationController
from ckan import model
from ckan import plugins as p
import ckan.lib.helpers as helpers

from ckanext.glasgow.logic.action import (
    ECAPINotAuthorized,
    ECAPIError,
)


class OrgController(OrganizationController):
    def read(self, organization_id, limit=20):
        pending_task = p.toolkit.get_action('pending_task_for_organization')({
            'ignore_auth': True}, {'organization_id': organization_id})

        if (pending_task and
                pending_task['task_type'] == 'organization_request_create'):
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
            return p.toolkit.render('organization/read_pending.html',
                                    extra_vars=vars)
        else:
            return super(OrgController, self).read(organization_id, limit)

    def new(self, data=None, errors=None, error_summary=None):
        return super(OrgController, self).new(data, errors, error_summary)

    def organization_change_requests(self, organization_name):
        context = {
            'model': model,
            'session': model.Session,
        }
        try:
            org = p.toolkit.get_action('organization_show')(context, {'id': organization_name})
        except p.toolkit.ObjectNotFound:
            return p.toolkit.abort(404, p.toolkit._('Organization not found'))

        try:
            task = p.toolkit.get_action('pending_task_for_organization')(context,
                {'name': organization_name, 'organization_id': org['id']})
            if task:
                task_value = json.loads(task['value'])
                request_status = p.toolkit.get_action('get_change_request')(context,
                    {'id': task_value.get('request_id')})
            else:
                request_status = None
        except p.toolkit.ValidationError, e:
            helpers.flash_error('{0}'.format(e.error_dict['message']))
        except ECAPIError:
            helpers.flash_error('{0}'.format(e.error_dict['message']))
        except p.toolkit.NotAuthorized:
            return p.toolkit.abort(401, p.toolkit._('Not authorized to view change requests'))

        c.group_dict = org

        return p.toolkit.render('organization/change_request_list.html',
                                extra_vars={'organization': org,
                                            'change_request': request_status,
                                            'task': task,
                                            })
