import nose

import ckanext.glasgow.logic.schema as custom_schema

eq_ = nose.tools.eq_


class TestSchemaConversion(object):

    def test_convert_ckan_dataset_to_ec_dataset(self):

        ckan_dict = {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'notes': 'Some longer description',
            'maintainer': 'Test maintainer',
            'maintainer_email': 'Test maintainer email',
            'license_id': 'OGL-UK-2.0',
            'tags': [
                {'name': 'Test tag 1'},
                {'name': 'Test tag 2'},
            ],
            'openness_rating': 3,
            'quality': 5,
            'published_on_behalf_of': 'Test published on behalf of',
            'usage_guidance': 'Test usage guidance',
            'category': 'Test category',
            'theme': 'Test theme',
            'standard_name': 'Test standard name',
            'standard_rating': 5,
            'standard_version': 'Test standard version',
        }

        ec_dict = custom_schema.convert_ckan_dataset_to_ec_dataset(ckan_dict)

        eq_(ec_dict['Title'], 'Test Dataset')
        eq_(ec_dict['Description'], 'Some longer description')
        eq_(ec_dict['MaintainerName'], 'Test maintainer')
        eq_(ec_dict['MaintainerContact'], 'Test maintainer email')
        eq_(ec_dict['License'], 'OGL-UK-2.0')
        eq_(ec_dict['Tags'], 'Test tag 1,Test tag 2')
        eq_(ec_dict['OpennessRating'], 3)
        eq_(ec_dict['Quality'], 5)
        eq_(ec_dict['PublishedOnBehalfOf'], 'Test published on behalf of')
        eq_(ec_dict['UsageGuidance'], 'Test usage guidance')
        eq_(ec_dict['Category'], 'Test category')
        eq_(ec_dict['Theme'], 'Test theme')
        eq_(ec_dict['StandardName'], 'Test standard name')
        eq_(ec_dict['StandardRating'], 5)
        eq_(ec_dict['StandardVersion'], 'Test standard version')

    def test_convert_ec_dataset_to_ckan_dataset(self):

        ec_dict = {
            'Title': 'Test Dataset',
            'Description': 'Some longer description',
            'MaintainerName': 'Test maintainer',
            'MaintainerContact': 'Test maintainer email',
            'License': 'OGL-UK-2.0',
            'Tags': 'Test tag 1,Test tag 2',
            'OpennessRating': 3,
            'Quality': 5,
            'PublishedOnBehalfOf': 'Test published on behalf of',
            'UsageGuidance': 'Test usage guidance',
            'Category': 'Test category',
            'Theme': 'Test theme',
            'StandardName': 'Test standard name',
            'StandardRating': 5,
            'StandardVersion': 'Test standard version',
        }

        ckan_dict = custom_schema.convert_ec_dataset_to_ckan_dataset(ec_dict)

        eq_(ckan_dict['title'], 'Test Dataset')
        eq_(ckan_dict['notes'], 'Some longer description')
        eq_(ckan_dict['maintainer'], 'Test maintainer')
        eq_(ckan_dict['maintainer_email'], 'Test maintainer email')
        eq_(ckan_dict['license_id'], 'OGL-UK-2.0')
        eq_(ckan_dict['tags'], [
            {'name': 'Test tag 1'},
            {'name': 'Test tag 2'},
            ])
        eq_(ckan_dict['openness_rating'], 3)
        eq_(ckan_dict['quality'], 5)
        eq_(ckan_dict['published_on_behalf_of'], 'Test published on behalf of')
        eq_(ckan_dict['usage_guidance'], 'Test usage guidance')
        eq_(ckan_dict['category'], 'Test category')
        eq_(ckan_dict['theme'], 'Test theme')
        eq_(ckan_dict['standard_name'], 'Test standard name')
        eq_(ckan_dict['standard_rating'], 5)
        eq_(ckan_dict['standard_version'], 'Test standard version')

    def test_convert_ckan_resource_to_ec_file(self):

        ckan_dict = {
            'package_id': 'test_dataset_id',
            'name': 'Test File name',
            'description': 'Some longer description',
            'format': 'application/csv',
            'license_id': 'uk-ogl',
            'openness_rating': 3,
            'quality': 5,
            'standard_name': 'Test standard name',
            'standard_rating': 1,
            'standard_version': 'Test standard version',
            'creation_date': '2014-03-22T05:42:00',
        }

        ec_dict = custom_schema.convert_ckan_resource_to_ec_file(ckan_dict)

        eq_(ec_dict['DatasetId'], 'test_dataset_id')
        eq_(ec_dict['Title'], 'Test File name')
        eq_(ec_dict['Description'], 'Some longer description')
        eq_(ec_dict['Type'], 'application/csv')
        eq_(ec_dict['License'], 'uk-ogl')
        eq_(ec_dict['OpennessRating'], 3)
        eq_(ec_dict['Quality'], 5)
        eq_(ec_dict['StandardName'], 'Test standard name')
        eq_(ec_dict['StandardRating'], 1)
        eq_(ec_dict['StandardVersion'], 'Test standard version')
        eq_(ec_dict['CreationDate'], '2014-03-22T05:42:00')

    def test_convert_ec_file_to_ckan_resource(self):

        ec_dict = {
            'DatasetId': 'test_dataset_id',
            'Title': 'Test File name',
            'Description': 'Some longer description',
            'Type': 'application/csv',
            'License': 'uk-ogl',
            'OpennessRating': 3,
            'Quality': 5,
            'StandardName': 'Test standard name',
            'StandardRating': 1,
            'StandardVersion': 'Test standard version',
            'CreationDate': '2014-03-22T05:42:00',
        }

        ckan_dict = custom_schema.convert_ec_file_to_ckan_resource(ec_dict)

        eq_(ckan_dict['package_id'], 'test_dataset_id')
        eq_(ckan_dict['name'], 'Test File name')
        eq_(ckan_dict['description'], 'Some longer description')
        eq_(ckan_dict['format'], 'application/csv')
        eq_(ckan_dict['license_id'], 'uk-ogl')
        eq_(ckan_dict['openness_rating'], 3)
        eq_(ckan_dict['quality'], 5)
        eq_(ckan_dict['standard_name'], 'Test standard name')
        eq_(ckan_dict['standard_rating'], 1)
        eq_(ckan_dict['standard_version'], 'Test standard version')
        eq_(ckan_dict['creation_date'], '2014-03-22T05:42:00')
