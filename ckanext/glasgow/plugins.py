import logging

import ckan.plugins as p

import ckanext.glasgow.logic.schema as custom_schema

log = logging.getLogger(__name__)


class GlasgowSchemaPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)

    # IConfigurer

    def update_config(self, config):

        # Check that we are running the correct CKAN version
        p.toolkit.requires_ckan_version('2.2')

        # Register the extension template dir
        p.toolkit.add_template_directory(config, 'theme/templates')

    # IDatasetForm

    def package_types(self):
        return ['dataset']

    def is_fallback(self):
        return True

    def create_package_schema(self):
        return custom_schema.create_package_schema()

    def update_package_schema(self):
        return custom_schema.update_package_schema()

    def show_package_schema(self):
        return custom_schema.show_package_schema()

    # IActions

    def get_actions(self):
        import ckanext.glasgow.logic.action as custom_actions

        function_names = (
            'dataset_request_create',
            'dataset_request_update',
            'pending_task_for_dataset',
        )
        return _get_module_functions(custom_actions, function_names)

    # IAuthFunctions

    def get_auth_functions(self):
        import ckanext.glasgow.logic.auth as custom_auth

        function_names = (
            'dataset_request_create',
            'dataset_request_update',
            'pending_task_for_dataset',
            'task_status_show',
        )
        return _get_module_functions(custom_auth, function_names)


def _get_module_functions(module, function_names):
    functions = {}
    for f in function_names:
        functions[f] = module.__dict__[f]

    return functions
