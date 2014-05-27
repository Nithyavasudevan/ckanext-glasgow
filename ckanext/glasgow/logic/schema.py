from ckan.logic.schema import (
    default_create_package_schema,
    default_update_package_schema,
    default_show_package_schema)

import ckan.plugins as p

from ckanext.glasgow.logic.validators import (
    string_max_length,
    tags_max_length,
    int_validator,
    int_range,
    trim_string,
)


# Reference some stuff from the plugins toolkit
_ = p.toolkit._
Invalid = p.toolkit.Invalid
get_validator = p.toolkit.get_validator
get_converter = p.toolkit.get_converter

ckan_to_ec_dataset_mapping = {
    'title': 'Title',
    'notes': 'Description',
    'maintainer': 'MaintainerName',
    'maintainer_email': 'MaintainerContact',
    'license_id': 'License',
    'openness_rating': 'OpennessRating',
    'quality': 'Quality',
    'tags': 'Tags',
    'published_on_behalf_of': 'PublishedOnBehalfOf',
    'usage_guidance': 'UsageGuidance',
    'category': 'Category',
    'theme': 'Theme',
    'standard_rating': 'StandardRating',
    'standard_name': 'StandardName',
    'standard_version': 'StandardVersion',
}


def convert_ckan_dataset_to_ec_dataset(ckan_dict):

    ec_dict = {}

    for ckan_name, ec_name in ckan_to_ec_dataset_mapping.iteritems():
        if ckan_name != 'tags' and ckan_dict.get(ckan_name):
            ec_dict[ec_name] = ckan_dict.get(ckan_name)

    if ckan_dict.get('tags'):
        ec_dict['Tags'] = ','.join([tag['name'] for tag in ckan_dict['tags']])

    return ec_dict


def convert_ec_dataset_to_ckan_dataset(ec_dict):

    ckan_dict = {}

    for ckan_name, ec_name in ckan_to_ec_dataset_mapping.iteritems():
        if ec_name != 'Tags' and ec_dict.get(ec_name):
            ckan_dict[ckan_name] = ec_dict.get(ec_name)

    if ec_dict.get('Tags'):
        ckan_dict['tags'] = [{'name': tag}
                             for tag in ec_dict['Tags'].split(',')]

    return ckan_dict


def create_package_schema():
    schema = default_create_package_schema()

    _modify_schema(schema)

    return schema


def update_package_schema():
    schema = default_update_package_schema()

    _modify_schema(schema)

    return schema


def _modify_schema(schema):

    # Core validators and converters
    not_empty = get_validator('not_empty')
    ignore_missing = get_validator('ignore_missing')
    name_validator = get_validator('name_validator')
    package_name_validator = get_validator('package_name_validator')
    convert_to_extras = get_converter('convert_to_extras')

    # Mandatory fields

    schema['__before'] = [tags_max_length(64000)]

    schema['name'] = [not_empty, unicode, trim_string(100), name_validator,
                      package_name_validator]

    schema['title'] = [not_empty, string_max_length(255), unicode]

    schema['notes'] = [not_empty, string_max_length(4000), unicode]

    schema['maintainer'] = [not_empty, string_max_length(255), unicode]

    schema['maintainer_email'] = [not_empty, string_max_length(255), unicode]

    # TODO: Populate license title or just use id
    schema['license_id'] = [not_empty, unicode]

    schema['openness_rating'] = [not_empty, int_validator, int_range(0, 5),
                                 convert_to_extras]

    schema['quality'] = [not_empty, int_validator, int_range(0, 5),
                         convert_to_extras]

    # Optional fields

    schema['published_on_behalf_of'] = [ignore_missing,
                                        string_max_length(255), unicode,
                                        convert_to_extras]

    schema['usage_guidance'] = [ignore_missing, string_max_length(255),
                                unicode, convert_to_extras]

    schema['category'] = [ignore_missing, string_max_length(255), unicode,
                          convert_to_extras]

    schema['theme'] = [ignore_missing, string_max_length(255), unicode,
                       convert_to_extras]

    schema['standard_name'] = [ignore_missing, string_max_length(255),
                               unicode, convert_to_extras]

    schema['standard_rating'] = [ignore_missing, int_validator,
                                 int_range(0, 5), convert_to_extras]

    schema['standard_version'] = [ignore_missing, string_max_length(255),
                                  unicode, convert_to_extras]


def show_package_schema():

    schema = default_show_package_schema()

    convert_from_extras = get_converter('convert_from_extras')

    schema['openness_rating'] = [convert_from_extras]

    schema['quality'] = [convert_from_extras]

    schema['published_on_behalf_of'] = [convert_from_extras]

    schema['usage_guidance'] = [convert_from_extras]

    schema['category'] = [convert_from_extras]

    schema['theme'] = [convert_from_extras]

    schema['standard_name'] = [convert_from_extras]

    schema['standard_rating'] = [convert_from_extras]

    schema['standard_version'] = [convert_from_extras]

    return schema
