import nose

import ckan.plugins as p

from ckanext.glasgow.logic import validators

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
        valid_values = [0, 3, 5]
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
