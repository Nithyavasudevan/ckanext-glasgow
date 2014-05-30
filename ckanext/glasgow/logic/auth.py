import ckan.plugins as p

import ckan.logic.auth as auth_core


def package_create(context, data_dict):

    if context.get('local_action', False):
        return {'success': False,
                'msg': 'Only sysadmins can create datasets directly into CKAN'
                }
    else:

        return dataset_request_create(context, data_dict)


def dataset_request_create(context, data_dict):

    return auth_core.create.package_create(context, data_dict)


def dataset_request_update(context, data_dict):

    return auth_core.update.package_create(context, data_dict)


def task_status_show(context, data_dict):
    return {'success': False,
            'msg': 'Only sysadmins can see task statuses'}


def pending_task_for_dataset(context, data_dict):
    return {'success': False,
            'msg': 'Only sysadmins can see task statuses'}
