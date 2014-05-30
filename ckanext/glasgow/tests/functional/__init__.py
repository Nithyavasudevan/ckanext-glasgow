import webtest
from pylons import config

import ckan


def get_test_app():
    '''Return a webtest.TestApp for CKAN
    '''
    config['ckan.legacy_templates'] = False
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app
