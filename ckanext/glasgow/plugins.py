import logging

import ckan.plugins as p

import ckanext.glasgow.logic.schema as custom_schema

log = logging.getLogger(__name__)


class GlasgowSchemaPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):

    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)

    # IRoutes

    def before_map(self, map):

        controller = 'ckanext.glasgow.controllers.dataset:DatasetController'

        map.connect('add dataset', '/dataset/new', controller=controller,
                    action='new')
        map.connect('/dataset/new_resource/{id}', controller=controller,
                    action='new_resource')
        map.connect('dataset_read', '/dataset/{id}',
                    controller=controller,
                    action='read',
                    ckan_icon='sitemap'
                    )
        map.connect('auth token', '/auth_token', controller=controller,
                    action='auth_token')

        map.connect('/dataset/{dataset}/resource/{resource}/version/{version}',
                    controller=controller,
                    action='resource_version')
        return map

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
            'package_create',
            'resource_create',
            'dataset_request_create',
            'file_request_create',
            'dataset_request_update',
            'pending_task_for_dataset',
            'resource_version_show',
            'check_for_task_status_update',
        )
        return _get_module_functions(custom_actions, function_names)

    # IAuthFunctions

    def get_auth_functions(self):
        import ckanext.glasgow.logic.auth as custom_auth

        function_names = (
            'package_create',
            'dataset_request_create',
            'file_request_create',
            'dataset_request_update',
            'pending_task_for_dataset',
            'task_status_show',
        )
        return _get_module_functions(custom_auth, function_names)

    # ITemplateHelpers

    def get_helpers(self):
        import ckanext.glasgow.helpers as custom_helpers

        function_names = (
            'get_licenses',
            'get_resource_versions',
        )
        return _get_module_functions(custom_helpers, function_names)


def _get_module_functions(module, function_names):
    functions = {}
    for f in function_names:
        functions[f] = module.__dict__[f]

    return functions
