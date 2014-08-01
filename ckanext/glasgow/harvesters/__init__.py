import slugify

from ckan import plugins as p
from ckan import model

from ckanext.harvest.harvesters.base import HarvesterBase

from ckanext.glasgow.logic.action import _expire_task_status


class EcHarvester(HarvesterBase):

    _user_name = None

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
        return p.toolkit.get_action('get_site_user')(
            {
                'ignore_auth': True,
                'defer_commit': True
            }, {})

    def _get_user_name(self):
        if self._user_name:
            return self._user_name

        user = self._get_site_user()
        self._user_name = user['name']

        return self._user_name


def get_initial_dataset_name(data_dict, field='title'):

    name = slugify.slugify(data_dict[field])

    existing_dataset = model.Package.Session.query(model.Package).filter_by(
        name=name).first()

    if existing_dataset:
        org_id = data_dict.get('owner_org')

        if org_id:
            name = '-'.join([name, str(org_id)[:4]])

    return name


def get_org_name(data_dict, field='title'):

    name = slugify.slugify(data_dict[field])

    return name


def get_dataset_name_from_task(context, audit_dict):

    request_id = audit_dict.get('RequestId')

    if not request_id:
        return

    task = get_task_for_request_id(context, request_id)

    if task:
        name = task.key
        if '@' in name:
            name = name.split('@')[0]

        _expire_task_status(context, task.id)

        return name

    return


def get_task_for_request_id(context, request_id):

    model = context['model']

    task = model.Session.query(model.TaskStatus) \
        .filter(model.TaskStatus.value.like('%{0}%'.format(request_id))) \
        .first()

    return task
