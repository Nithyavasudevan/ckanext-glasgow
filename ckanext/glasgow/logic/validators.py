import cgi
import datetime
from itertools import count

from dateutil.parser import parse as date_parser

import ckan.plugins as p

# Reference some stuff from the toolkit
_ = p.toolkit._
Invalid = p.toolkit.Invalid
get_validator = p.toolkit.get_validator
get_converter = p.toolkit.get_converter


def no_pending_dataset_with_same_name(value, context):
    '''
    Checks if there is a pending request for a dataset with the same name

    :raises: :py:exc:`~ckan.plugins.toolkit.Invalid` if there is a pending
        request with the same dataset name

    '''
    pending_task = p.toolkit.get_action('pending_task_for_dataset')({
        'ignore_auth': True}, {'name': value})

    if pending_task:
        raise Invalid(
            _('There is a pending request for a dataset with the same name')
        )
    return value


def string_max_length(max_length):
    '''
    Checks if a string is longer than a certain length

    :raises: ckan.lib.navl.dictization_functions.Invalid if the string is
        longer than max length
    '''
    def callable(value, context):

        if len(value) > max_length:
            raise Invalid(
                _('Length must be less than {0} characters')
                .format(max_length)
            )

        return value

    return callable


def tags_max_length(max_length):
    '''
    Checks if the combined lenght of all tags is longer than a
    certain length

    :raises: ckan.lib.navl.dictization_functions.Invalid if the strings are
        longer than max length
    '''
    def callable(key, data, errors, context):

        total_length = 0

        for key in data.keys():
            if key[0] == 'tags' and key[2] == 'name':
                total_length += len(data[key])

        if total_length > max_length:
            raise Invalid(
                _('Combined length of tags must be less than {0} characters')
                .format(max_length)
            )

    return callable


# Copied from master (2.3a) as this is not yet in 2.2 (See #1692)
def int_validator(value, context):
    '''
    Return an integer for value, which may be a string in base 10 or
    a numeric type (e.g. int, long, float, Decimal, Fraction). Return
    None for None or empty/all-whitespace string values.

    :raises: ckan.lib.navl.dictization_functions.Invalid for other
        inputs or non-whole values
    '''
    if value is None:
        return None
    if hasattr(value, 'strip') and not value.strip():
        return None

    try:
        whole, part = divmod(value, 1)
    except TypeError:
        try:
            return int(value)
        except ValueError:
            pass
    else:
        if not part:
            try:
                return int(whole)
            except TypeError:
                pass  # complex number: fail like int(complex) does

    raise Invalid(_('Invalid integer'))


def int_range(min_value=0, max_value=5):
    '''
        Checks if an integer is included between minimum and maximum values
        (included).

        Does *not* check if the value is actually an integer, so
        `int_validator` must be called before this validator.

        If no value provided, validation passes.

        :raises: ckan.lib.navl.dictization_functions.Invalid if the value is
        not within the range
    '''
    def callable(value, context):

        if value and not (value >= min_value and value <= max_value):
            raise Invalid(
                _('Value must be an integer between {0} and {1}')
                .format(min_value, max_value)
            )
        return value

    return callable


def trim_string(max_length):
    '''
    Trims a string up to a defined length

    '''
    def callable(value, context):

        if isinstance(value, basestring) and len(value) > max_length:
            value = value[:max_length]
        return value
    return callable


def iso_date(value, context):
    '''
    Checks if the value can be interpreted as an ISO 8601 date representation

    :raises: :py:exc:`~ckan.plugins.toolkit.Invalid` if the value could not be
        transformed to ISO 8601

    '''
    if not value:
        return value
    default_date = datetime.datetime(
        datetime.datetime.today().year, 1, 1, 0, 0, 0)
    try:
        date_value = date_parser(value, default=default_date)
    except ValueError:
        raise Invalid(_('Invalid date'))
    return date_value.isoformat()


def url_or_upload_not_empty(key, data, errors, context):

    if len(key) == 1:
        # Single resource
        url_key = ('url', )
        upload_key = ('upload', )
    elif len(key) == 3:
        # Part of a dataset
        index = key[1]
        url_key = ('resources', index, 'url')
        upload_key = ('resources', index, 'upload')

    check_url = (key == url_key
                 and not data.get(url_key)
                 and not isinstance(data.get(upload_key), cgi.FieldStorage))

    check_upload = (key == upload_key
                    and not isinstance(data.get(upload_key),
                                       cgi.FieldStorage)
                    and not data.get(url_key))

    check_none = (not isinstance(data.get(upload_key), cgi.FieldStorage)
                  and not data.get(url_key))

    check_both = (isinstance(data.get(upload_key), cgi.FieldStorage)
                  and data.get(url_key))

    if (check_url or check_upload or check_none or check_both):
        raise Invalid(_('Please provide either a file upload or a URL'))


def tag_string_convert(key, data, errors, context):
    '''Takes a list of tags that is a comma-separated string (in data[key])
    and parses tag names. These are added to the data dict, enumerated. They
    are also validated.'''

    if isinstance(data[key], basestring):
        tags = [tag.strip()
                for tag in data[key].split(',')
                if tag.strip()]
    else:
        tags = data[key]

    current_index = max([int(k[1])
                         for k in data.keys()
                         if len(k) == 3 and k[0] == 'tags'] + [-1])

    for num, tag in zip(count(current_index+1), tags):
        data[('tags', num, 'name')] = tag
