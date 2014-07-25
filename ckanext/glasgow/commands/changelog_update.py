import sys
import logging

from sqlalchemy import or_

from ckan import model
from ckan.lib.cli import CkanCommand
from ckan.plugins import toolkit

from ckanext.glasgow.model import HarvestLastAudit, harvest_last_audit_table
from ckanext.glasgow.logic.action import ECAPIError
from ckanext.glasgow.harvesters.changelog import save_last_audit_id


class UpdateFromEcApiChangeLog(CkanCommand):
    summary = "--NO SUMMARY--"
    usage = "--NO USAGE--"

    def command(self):
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


class ChangelogAudit(CkanCommand):
    '''Manages Audits for the Changelog Harvesting

    Usage:

      changelog_audit clear
        - Clear all audits (ie next harvest will start from audit 0).

      changelog_audit set [audit_id]
        - Sets the next audit to start from. If audit_id is omitted the most
          recent one on the platform will be used.


    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):

        self._load_config()
        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)

        cmd = self.args[0]
        if cmd == 'clear':
            self._clear()
        elif cmd == 'set':
            audit_id = self.args[1] if len(self.args) > 1 else None
            self._set(audit_id)

    def _clear(self):
        model.Session.execute(harvest_last_audit_table.delete())
        model.Session.commit()
        print 'Last audits table emptied'

    def _set(self, audit_id=None):

        context = {
            'ignore_auth': True,
        }
        if not audit_id:
            audits = toolkit.get_action('changelog_show')(context, {})
            if not audits:
                print 'Could not get most recent audits'
                sys.exit(1)

            audit_id = audits[0]['AuditId']

        save_last_audit_id(audit_id, None)

        print 'Set last audit id to', audit_id
