import logging

import ckan.plugins as p

import ckanext.glasgow.logic.schema as custom_schema

log = logging.getLogger(__name__)


class GlasgowSchemaPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IDatasetForm, inherit=True)

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
