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
