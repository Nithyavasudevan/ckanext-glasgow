import cgi
import nose
import datetime

import ckan.plugins as p
import ckan.new_tests.helpers as helpers

from ckanext.glasgow.logic import validators
from ckanext.glasgow.logic.action import (
    _create_task_status,
)


# 2.3 will offer navl_validate in toolkit
from ckan.lib.navl.dictization_functions import validate

eq_ = nose.tools.eq_


class TestValidators(object):

    def test_string_max_length_valid(self):

        value = 'short_string'
        context = {}
        validator = validators.string_max_length(20)

        new_value = validator(value, context)

        eq_(new_value, value)

    def test_string_max_length_invalid(self):

        value = 'long_string_is_longer_than_allowed'
        context = {}
        validator = validators.string_max_length(20)

        nose.tools.assert_raises(p.toolkit.Invalid, validator, value, context)

    def test_tags_max_length_valid(self):

        data_dict = {
            'tags': [{'name': 'test_tag_1'}, {'name': 'test_tag_2'}]
        }
        schema = {
            '__before': [validators.tags_max_length(20)],
            'tags': {'name': []},
        }
        context = {}

        data, errors = validate(data_dict, schema, context)

        eq_(errors, {})

    def test_tags_max_length_invalid(self):

        data_dict = {
            'tags': [{'name': 'test_tag_1'}, {'name': 'test_tag_2'}]
        }
        schema = {
            '__before': [validators.tags_max_length(10)],
            'tags': {'name': []},
        }
        context = {}

        data, errors = validate(data_dict, schema, context)

        eq_(errors['__before'],
            ['Combined length of tags must be less than 10 characters'])

    def test_int_validator_valid(self):

        valid_values = [0, -2, 3, 4.00, '5', '+6']
        context = {}

        for value in valid_values:
            validators.int_validator(value, context)

    def test_int_validator_invalid(self):

        invalid_values = ['12.3', 'a', '1e6']
        context = {}

        for value in invalid_values:
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.int_validator, value, context)

    def test_int_range_valid(self):

        validator = validators.int_range(0, 5)
        valid_values = [None, '', 0, 3, 5]
        context = {}

        for value in valid_values:
            new_value = validator(value, context)

            eq_(new_value, value)

    def test_int_range_invalid(self):

        validator = validators.int_range(0, 5)
        invalid_values = [-1, 6, 10]
        context = {}

        for value in invalid_values:
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validator, value, context)

    def test_trim_string(self):

        value = 'long_string_is_longer_than_allowed'
        context = {}
        validator = validators.trim_string(11)
        new_value = validator(value, context)

        eq_(new_value, 'long_string')

    def test_iso_date_valid(self):

        values = [
            '2014',
            '2014-03',
            'March 2014',
            '2014-03-22T05:42:00',
        ]
        context = {}
        for value in values:
            new_value = validators.iso_date(value, context)

            # Check it returns a valid datetime
            datetime.datetime.strptime(new_value, '%Y-%m-%dT%H:%M:%S')

    def test_iso_date_invalid(self):

        values = [
            'xaaee',
            'Test 2013',
            '2014-13',
            '13999-03-22T05:42:00',
        ]
        context = {}
        for value in values:
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.iso_date, value, context)

    def test_url_or_upload_not_empty_upload_only(self):

        mock_upload = cgi.FieldStorage()
        data = {
            ('upload',): mock_upload,
            ('url',): '',
        }
        errors = {}
        context = {}

        for key in (('upload', ), ('url', )):
            validators.url_or_upload_not_empty(key, data, errors, context)

    def test_url_or_upload_not_empty_url_only(self):

        data = {
            ('upload',): '',
            ('url',): 'http://some.url',
        }
        errors = {}
        context = {}

        for key in (('upload', ), ('url', )):
            validators.url_or_upload_not_empty(key, data, errors, context)

    def test_url_or_upload_not_empty_upload_not_a_file(self):

        data = {
            ('upload',): 'text',
            ('url',): '',
        }
        errors = {}
        context = {}

        for key in (('upload', ), ('url', )):
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.url_or_upload_not_empty,
                                     key, data, errors, context)

    def test_url_or_upload_not_empty_none(self):

        data = {
            ('upload',): '',
            ('url',): '',
        }
        errors = {}
        context = {}

        for key in (('upload', ), ('url', )):
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.url_or_upload_not_empty,
                                     key, data, errors, context)

    def test_url_or_upload_not_empty_both(self):

        mock_upload = cgi.FieldStorage()
        data = {
            ('upload',): mock_upload,
            ('url',): 'http://some.url',
        }
        errors = {}
        context = {}

        for key in (('upload', ), ('url', )):
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.url_or_upload_not_empty,
                                     key, data, errors, context)

    def test_url_or_upload_not_empty_upload_only_flattened(self):

        mock_upload = cgi.FieldStorage()
        data = {
            ('resources', 0, 'upload'): mock_upload,
            ('resources', 0, 'url'): '',
        }
        errors = {}
        context = {}

        for key in (('resources', 0, 'upload'), ('resources', 0, 'url')):
            validators.url_or_upload_not_empty(key, data, errors, context)

    def test_url_or_upload_not_empty_url_only_flattened(self):

        data = {
            ('resources', 0, 'upload'): '',
            ('resources', 0, 'url'): 'http://some.url',
        }
        errors = {}
        context = {}

        for key in (('resources', 0, 'upload'), ('resources', 0, 'url')):
            validators.url_or_upload_not_empty(key, data, errors, context)

    def test_url_or_upload_not_empty_upload_not_a_file_flattened(self):

        data = {
            ('resources', 0, 'upload'): 'text',
            ('resources', 0, 'url'): '',
        }
        errors = {}
        context = {}

        for key in (('resources', 0, 'upload'), ('resources', 0, 'url')):
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.url_or_upload_not_empty,
                                     key, data, errors, context)

    def test_url_or_upload_not_empty_none_flattened(self):

        data = {
            ('resources', 0, 'upload'): '',
            ('resources', 0, 'url'): '',
        }
        errors = {}
        context = {}

        for key in (('resources', 0, 'upload'), ('resources', 0, 'url')):
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.url_or_upload_not_empty,
                                     key, data, errors, context)

    def test_url_or_upload_not_empty_both_flattened(self):

        mock_upload = cgi.FieldStorage()
        data = {
            ('resources', 0, 'upload'): mock_upload,
            ('resources', 0, 'url'): 'http://some.url',
        }
        errors = {}
        context = {}

        for key in (('resources', 0, 'upload'), ('resources', 0, 'url')):
            nose.tools.assert_raises(p.toolkit.Invalid,
                                     validators.url_or_upload_not_empty,
                                     key, data, errors, context)

class TestNameValidators(object):

    def setup(cls):
        helpers.reset_db()

    def test_no_pending_dataset_with_same_name_valid(self):

        value = 'test_dataset_name'
        context = {}
        new_value = validators.no_pending_dataset_with_same_name(value,
                                                                 context)
        eq_(new_value, value)

    def test_no_pending_dataset_with_same_name_invalid(self):

        task_dict = _create_task_status({'user': 'test'},
                                        task_type='test_task_type',
                                        entity_id='test_dataset_id',
                                        entity_type='dataset',
                                        key='test_dataset_name',
                                        value='test_value'
                                        )

        value = 'test_dataset_name'
        context = {}
        nose.tools.assert_raises(p.toolkit.Invalid,
                                 validators.no_pending_dataset_with_same_name,
                                 value, context)
