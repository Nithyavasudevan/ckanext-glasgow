import json
import mock

import nose.tools as nt

import ckan.new_tests.helpers as helpers
import ckan.new_tests.factories as factories

import ckanext.harvest.model as harvest_model
from ckanext.harvest.tests.factories import HarvestJobFactory

from ckanext.glasgow.harvesters.ec_harvester import EcHarvester
from ckanext.glasgow.tests import run_mock_ec


class TestDatasetCreate(object):

    @classmethod
    def setup_class(cls):

        helpers.reset_db()

        # Create test user
        cls.normal_user = helpers.call_action('user_create',
                                              name='normal_user',
                                              email='test@test.com',
                                              password='test')

        # Start mock EC API
        harvest_model.setup()
        run_mock_ec()


    def test_create_orgs(self):
        harvester = EcHarvester()
        job = HarvestJobFactory()
        orgs = harvester._create_orgs(job)
        nt.assert_equals(len(orgs), 3)

    def test_gather(self):
        harvester = EcHarvester()
        job = HarvestJobFactory()
        harvester.gather_stage(job)

        nt.assert_equals(len(job.objects), 3)

    @mock.patch('requests.get')
    def test_gather_with_ec_500_response(self, m):
        # setup a mock for requests.get that returns an object
        # with a status_code of 500
        req = mock.MagicMock()
        req.status_code = 500
        m.return_value = req

        harvester = EcHarvester()
        job = HarvestJobFactory()
        
        nt.assert_equals(False, harvester.gather_stage(job))

    @mock.patch('requests.get')
    def test_gather_with_ec_failed_response(self, m):
        # simulate a api error response with error message
        req = mock.MagicMock()
        req.status_code = 200
        req.content = '''{
            "IsRetryRequested": false,
            "ErrorMessage": "an error occured",
            "IsErrorResponse": true,
            "MetadataResultSet": []}
        '''
        m.return_value = req

        harvester = EcHarvester()
        job = HarvestJobFactory()
        
        nt.assert_equals(False, harvester.gather_stage(job))

    def test_import(self):
        harvester = EcHarvester()
        job = HarvestJobFactory()
        factories.Organization(id='4', name='test-org')
        harvest_object = harvest_model.HarvestObject(
            guid='3',
            job=job,
            content=json.dumps({
                "Id": 3,
                "Metadata": {
                    "Category": "debitis",
                    "Description": "Sint perspiciatis et dolorem. Consectetur impedit porro omnis nisi adipisci eum rerum tenetur. Voluptate accusamus praesentium autem molestiae possimus a quibusdam harum.",
                    "License": "http://mayert.us/gibsondickinson/dicki.html",
                    "MaintainerContact": "nova_windler@swift.uk",
                    "MaintainerName": "Marge Conn",
                    "OpennessRating": "0",
                    "PublishedOnBehalfOf": "Ms. Gloria Bode",
                    "Quality": "3",
                    "StandardName": "Iste maxime ad non ea",
                    "StandardRating": "4",
                    "StandardVersion": "4.4.0",
                    "Tags": "beatae consequatur sunt ducimus mollitia",
                    "Title": "Raj Data Set 001",
                    "Theme": "assumenda",
                    "UsageGuidance": "Sed magnam labore voluptatem accusamus aut dicta eos et. Et omnis aliquam fugit sed iusto. Consectetur esse et tempora."
                    },
                "CreatedTime": "2014-06-09T14:08:08.78",
                "ModifiedTime": "2014-06-09T14:08:08.78",
                "OrganisationId": 4,
                "Title": "Raj Data Set 001"
                }))
        harvest_object.save()
        harvester.import_stage(harvest_object)
        pkg = helpers.call_action('package_show', name_or_id=u'raj-data-set-001')
        nt.assert_equals(pkg['title'], u'Raj Data Set 001')

        org = helpers.call_action('organization_show', id=u'4')
        nt.assert_equals(len(org['packages']), 1)
        nt.asssert_equals(org['packages'][0]['name'], u'raj-data-set-001')
