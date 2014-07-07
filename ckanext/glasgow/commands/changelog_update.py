import logging

from sqlalchemy import or_

from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit

from ckanext.glasgow.logic.action import ECAPIError

class UpdateFromEcApiChangeLog(CkanCommand):
    summary = "--NO SUMMARY--"
    usage = "--NO USAGE--"

    def command(self):
        from ckan import model
        self._load_config()
        pending_tasks = model.Session.query(model.TaskStatus) \
            .filter(or_(model.TaskStatus.state == 'in_progress',
                    model.TaskStatus.state == 'sent'))

        check_for_update = toolkit.get_action('check_for_task_status_update')
        for task in pending_tasks.all():
            context = {
                'model': model,
                'session': model.Session,
                'ignore_auth': True,
            }
            try:
                check_for_update(context, {'task_id': task.id})
                print 'updated task {0}'.format(task.id)
            except ECAPIError, e:
                print 'failed to update task {0}: {1}'.format(task.id,
                                                              e.extra_msg)


