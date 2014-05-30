import json

from ckan.controllers.package import PackageController

import ckan.plugins as p


class DatasetController(PackageController):

    def read(self, id, format='html'):

        pending_task = p.toolkit.get_action('pending_task_for_dataset')({
            'ignore_auth': True}, {'id': id})

        if (pending_task and
                pending_task['task_type'] == 'dataset_request_create'):
            pending_task['value'] = json.loads(pending_task['value'])
            vars = {
                'task': pending_task,
            }
            return p.toolkit.render('package/read_pending.html',
                                    extra_vars=vars)
        else:
            return super(DatasetController, self).read(id, format)
