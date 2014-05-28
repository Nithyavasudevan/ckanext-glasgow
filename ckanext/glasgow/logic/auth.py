import ckan.plugins as p

import ckan.logic.auth as auth_core


def dataset_request_create(context, data_dict):

    return auth_core.create.package_create(context, data_dict)


def dataset_request_update(context, data_dict):

    return auth_core.update.package_create(context, data_dict)
