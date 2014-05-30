import nose
import webtest

from pylons import config

import ckan
import ckan.new_tests.helpers as helpers

from ckanext.glasgow.tests import run_mock_ec

eq_ = nose.tools.eq_


def _get_test_app():
    '''Return a webtest.TestApp for CKAN
    '''
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app


class TestDatasetController(object):

    @classmethod
    def setup_class(cls):
        cls.app = _get_test_app()

        # Create test user
        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')
        # Start mock EC API
        run_mock_ec()

    def teardown(cls):
        helpers.reset_db()

    def test_pending_dataset_page(self):

        data_dict = {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
        }

        context = {'user': self.normal_user['name']}
        request_dict = helpers.call_action('dataset_request_create',
                                           context=context,
                                           **data_dict)

        assert 'request_id' in request_dict

        response = self.app.get('/dataset/test-dataset')
        eq_(response.status_int, 200)

        # Check that we got the pending page, not a default dataset page

        assert ('[Pending] {0}'.format(data_dict['title'])
                in response.html.head.title.text)

        # TODO: This is fragile, we may need to tweak once the UI is finalized
        assert request_dict['request_id'] in response.unicode_body
        assert request_dict['task_id'] in response.unicode_body

    def test_normal_dataset_page(self):

        data_dict = {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'openness_rating': 3,
            'quality': 5,
        }

        context = {'ignore_auth': True, 'local_action': True}
        dataset_dict = helpers.call_action('package_create',
                                           context=context,
                                           **data_dict)

        assert 'id' in dataset_dict

        response = self.app.get('/dataset/test-dataset')
        eq_(response.status_int, 200)

        # Check that we got the pending page, not a default dataset page

        assert (not '[Pending] {0}'.format(data_dict['title'])
                in response.html.head.title.text)
        assert (data_dict['title'] in response.html.head.title.text)
