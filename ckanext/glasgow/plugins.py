import logging

import ckan.plugins as p


log = logging.getLogger(__name__)

class GlasgowPlugin(p.SingletonPlugin):

    p.implements(p.IConfigurer, inherit=True)

    # IConfigurer
    def update_config(self, config):

        p.toolkit.requires_ckan_version('2.2')
