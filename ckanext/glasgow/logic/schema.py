from ckan.logic.schema import (
    default_create_package_schema,
    default_update_package_schema,
    default_show_package_schema,
    default_resource_schema,
    default_group_schema,
    )

import ckan.plugins as p

from ckanext.glasgow.logic.validators import (
    string_max_length,
    tags_max_length,
    int_validator,
    int_range,
    trim_string,
    iso_date,
    no_pending_dataset_with_same_name,
    no_pending_organization_with_same_name,
    url_or_upload_not_empty,
    tag_string_convert,
    unique_title_within_organization,
    no_pending_dataset_with_same_title_in_same_org,
    tag_length_validator,
)


# Reference some stuff from the plugins toolkit
_ = p.toolkit._
Invalid = p.toolkit.Invalid
get_validator = p.toolkit.get_validator
get_converter = p.toolkit.get_converter

# Core validators and converters
not_empty = get_validator('not_empty')
ignore_missing = get_validator('ignore_missing')

# CKAN to EC API mappings

ckan_to_ec_organization_mapping = {
    'id': 'Id',
    'title': 'Name',  #TODO: replace with Title when MS sort their stuff
    'needs_approval': 'NeedsApproval',
    'description': 'Description',
}

ckan_to_ec_dataset_mapping = {
    'id': 'Id',
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

ckan_to_ec_resource_mapping = {
    'id': 'FileId',
    'ec_api_dataset_id': 'DatasetId',
    'name': 'Title',
    'description': 'Description',
    'format': 'Type',
    'license_id': 'License',
    'openness_rating': 'OpennessRating',
    'quality': 'Quality',
    'standard_name': 'StandardName',
    'standard_rating': 'StandardRating',
    'standard_version': 'StandardVersion',
    'creation_date': 'CreationDate',
    'url': 'ExternalUrl',
}


def convert_ckan_organization_to_ec_organization(ckan_dict):

    ec_dict = {}

    for ckan_name, ec_name in ckan_to_ec_organization_mapping.iteritems():
        ec_dict[ec_name] = ckan_dict.get(ckan_name)

    return ec_dict


def convert_ec_organization_to_ckan_organization(ec_dict):

    ckan_dict = {}

    for ckan_name, ec_name in ckan_to_ec_organization_mapping.iteritems():
        ckan_dict[ckan_name] = ec_dict.get(ec_name)

    # Ask MS
    if not ckan_dict.get('title') and ec_dict.get('Title'):
        ckan_dict['title'] = ec_dict.get('Title')

    return ckan_dict


def convert_ckan_dataset_to_ec_dataset(ckan_dict):

    ec_dict = {}

    for ckan_name, ec_name in ckan_to_ec_dataset_mapping.iteritems():
        if ckan_name != 'tags' and ckan_name in ckan_dict:
            ec_dict[ec_name] = ckan_dict.get(ckan_name)

    if ckan_dict.get('tags'):
        ec_dict['Tags'] = ','.join([tag['name']
                                    for tag in ckan_dict['tags']])
    elif ckan_dict.get('tags_string'):
        ec_dict['Tags'] = ckan_dict.get('tags_string')

    return ec_dict


def convert_ec_dataset_to_ckan_dataset(ec_dict):

    ckan_dict = {}

    for ckan_name, ec_name in ckan_to_ec_dataset_mapping.iteritems():
        if ec_name != 'Tags' and ec_name in ec_dict:
            ckan_dict[ckan_name] = ec_dict.get(ec_name)

    if ec_dict.get('Tags'):
        ckan_dict['tags'] = [{'name': tag}
                             for tag in ec_dict['Tags'].split(',')]

    # Make sure ids are strings, otherwise we might get errors on update
    if ckan_dict.get('id'):
        ckan_dict['id'] = unicode(ckan_dict['id'])

    return ckan_dict


def convert_ckan_resource_to_ec_file(ckan_dict):

    ec_dict = {}

    for ckan_name, ec_name in ckan_to_ec_resource_mapping.iteritems():
        if ckan_dict.get(ckan_name):
            ec_dict[ec_name] = ckan_dict.get(ckan_name)

    if not ec_dict.get('DatasetId') and ckan_dict.get('package_id'):
        ec_dict['DatasetId'] = ckan_dict.get('package_id')

    return ec_dict


def convert_ec_file_to_ckan_resource(ec_dict):

    ckan_dict = {}

    for ckan_name, ec_name in ckan_to_ec_resource_mapping.iteritems():
        if ec_dict.get(ec_name):
            ckan_dict[ckan_name] = ec_dict.get(ec_name)

    return ckan_dict


def create_package_schema():
    schema = default_create_package_schema()

    _modify_schema(schema)

    return schema


def ec_create_package_schema():
    '''Schema for validated data dicts

    This schema is used for creation of the package after it has been sent to
    the EC platform and been succeesfully created there
    '''
    schema = create_package_schema()

    name_validator = get_validator('name_validator')
    package_name_validator = get_validator('package_name_validator')

    schema['name'] = [not_empty, unicode, trim_string(100), name_validator,
                      package_name_validator]
    return schema


def update_package_schema():
    schema = default_update_package_schema()

    _modify_schema(schema)
    name_validator = get_validator('name_validator')
    schema['name'] = [not_empty, unicode, trim_string(100), name_validator,
                      no_pending_dataset_with_same_name]

    return schema


def _modify_schema(schema):

    name_validator = get_validator('name_validator')
    package_name_validator = get_validator('package_name_validator')
    not_missing = get_validator('not_missing')
    ignore_empty = get_validator('ignore_empty')
    not_empty = get_validator('not_empty')

    convert_to_extras = get_converter('convert_to_extras')

    # Mandatory fields

    schema['__before'] = [tags_max_length(64000)]

    schema['id'] = [ignore_empty, unicode]

    schema['name'] = [not_empty, unicode, trim_string(100), name_validator,
                      package_name_validator,
                      no_pending_dataset_with_same_name]

    schema['title'] = [not_empty, string_max_length(255), unicode,
                       unique_title_within_organization,
                       no_pending_dataset_with_same_title_in_same_org,
                       ]

    schema['notes'] = [not_empty, string_max_length(4000), unicode]

    schema['maintainer'] = [not_empty, string_max_length(255), unicode]

    schema['maintainer_email'] = [not_empty, string_max_length(255), unicode]

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

    # Internal fields

    schema['ec_api_id'] = [ignore_missing, unicode,
                           convert_to_extras]

    schema['ec_api_org_id'] = [ignore_missing, unicode,
                               convert_to_extras]

    schema['resources'] = _modify_resource_schema()

    schema['tag_string'] = [ignore_missing, tag_string_convert]
    schema['tags']['name'] = [not_missing, not_empty, unicode,
                              tag_length_validator]


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

    schema['resources'] = resource_schema()

    # Internal fields

    schema['ec_api_id'] = [convert_from_extras]

    schema['ec_api_org_id'] = [convert_from_extras]


    return schema


def resource_schema():
    schema = _modify_resource_schema()
    schema.update({
        'package_id': [not_empty, unicode],
        'created':  [ignore_missing, iso_date, unicode],
        'last_modified': [ignore_missing, iso_date, unicode],
        'cache_last_updated': [ignore_missing, iso_date, unicode],
        'webstore_last_updated': [ignore_missing, iso_date, unicode],
    })
    return schema


def _modify_resource_schema():
    # Mandatory fields

    schema = default_resource_schema()

    schema['package_id'] = [ignore_missing]

    schema['name'] = [not_empty, string_max_length(255), unicode]

    schema['description'] = [not_empty, string_max_length(64000), unicode]

    schema['format'] = [not_empty, string_max_length(255), unicode]

    schema['url'] = [url_or_upload_not_empty, ignore_missing, unicode]

    schema['upload'] = [url_or_upload_not_empty, ignore_missing]

    # Optional fields

    schema['license_id'] = [ignore_missing, unicode]

    schema['openness_rating'] = [ignore_missing, int_validator, int_range(0, 5)
                                 ]

    schema['quality'] = [ignore_missing, int_validator, int_range(0, 5)]

    schema['standard_name'] = [ignore_missing, string_max_length(255), unicode]

    schema['standard_rating'] = [ignore_missing, int_validator, int_range(0, 5)
                                 ]

    schema['standard_version'] = [ignore_missing, string_max_length(255),
                                  unicode]

    schema['creation_date'] = [ignore_missing, iso_date, unicode]

    # Internal fields

    schema['ec_api_id'] = [ignore_missing, unicode]

    schema['ec_api_dataset_id'] = [ignore_missing, unicode]

    return schema


def create_group_schema():
    boolean_validator = get_validator('boolean_validator')
    not_missing = get_validator('not_missing')
    convert_to_extras = get_converter('convert_to_extras')
    name_validator = get_validator('name_validator')
    group_name_validator = get_validator('group_name_validator')
    schema = default_group_schema()
    schema.update({
        'name': [not_empty, unicode, name_validator, group_name_validator,
                 no_pending_organization_with_same_name],
        'needs_approval': [not_missing, boolean_validator, convert_to_extras]
    })
    return schema


def show_group_schema():
    boolean_validator = get_validator('boolean_validator')
    not_missing = get_validator('not_missing')
    convert_from_extras = get_converter('convert_from_extras')
    schema = default_group_schema()
    schema.update({'needs_approval': [not_missing, boolean_validator, convert_from_extras]})
    return schema
