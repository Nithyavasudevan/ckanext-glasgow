from ckan.logic.schema import (
    default_create_package_schema,
    default_update_package_schema,
    default_show_package_schema,
    default_resource_schema,
    default_group_schema,
    default_update_group_schema,
    default_user_schema,
    default_extras_schema,
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
    url_name_validator,
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
    'needs_approval': 'NeedsApproval',
}

ckan_to_ec_resource_mapping = {
    'id': 'FileId',
    'package_id': 'DatasetId',
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
    'url': 'FileExternalUrl',
    'external_url': 'ExternalUrl',
}


ckan_to_ec_user_mapping = {
    'id': 'UserId',
    'name': 'UserName',
    'fullname': 'DisplayName',
    'about': 'About',
    'email': 'Email',
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

    # Arbitrary extras
    ec_dict['Metadata'] = {}
    for extra in ckan_dict.get('extras', []):
        if extra['key'] not in ckan_dict and not extra['key'].startswith('harvest_'):
            ec_dict['Metadata'][extra['key']] = extra['value']

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

    # Arbitrary stuff stored as extras
    ec_keys = [v for k, v in ckan_to_ec_dataset_mapping.iteritems()]
    ckan_dict['extras'] = []
    for key, value in ec_dict.iteritems():
        if key not in ec_keys:
            ckan_dict['extras'].append({'key': key, 'value': value})

    return ckan_dict


def convert_ckan_resource_to_ec_file(ckan_dict):

    ec_dict = {}

    for ckan_name, ec_name in ckan_to_ec_resource_mapping.iteritems():
        if ckan_dict.get(ckan_name):
            ec_dict[ec_name] = ckan_dict.get(ckan_name)

    if not ec_dict.get('DatasetId') and ckan_dict.get('package_id'):
        ec_dict['DatasetId'] = ckan_dict.get('package_id')

    # Arbitrary extras
    ec_dict['Metadata'] = {}
    if isinstance(ckan_dict.get('extras'), list):
        for extra in ckan_dict['extras']:
            if extra['key'] not in ckan_dict:
                ec_dict['Metadata'][extra['key']] = extra['value']

    return ec_dict


def convert_ec_file_to_ckan_resource(ec_dict):

    ckan_dict = {}

    for ckan_name, ec_name in ckan_to_ec_resource_mapping.iteritems():
        if ec_dict.get(ec_name):
            ckan_dict[ckan_name] = ec_dict.get(ec_name)

    ec_keys = [v for k, v in ckan_to_ec_resource_mapping.iteritems()]
    for key, value in ec_dict.iteritems():
        if key not in ec_keys:
            ckan_dict[key] = value

    return ckan_dict


def convert_ckan_member_to_ec_member(ckan_dict):
    role_dict = {
        'admin': 'OrganisationAdmin',
        'editor': 'OrganisationEditor',
        'member': 'Member',
    }

    return {
        'NewOrganisationId': ckan_dict['id'],
        'UserRoles': [ role_dict.get(ckan_dict['role']) ],
    }

def convert_ec_member_to_ckan_member(ec_dict):
    role_dict = {
        'OrganisationAdmin': 'admin',
        'OrganisationEditor': 'editor',
        'Member': 'member',
    }

    try:
        return {
            'id': ec_dict['OrganisationId'],
            'role':  role_dict[ec_dict['Roles'][0]],
            'username': ec_dict['UserName'],
        }

    except (KeyError, IndexError), e:
        raise p.toolkit.ValidationError('cannot convert ec to ckan')


def convert_ec_user_to_ckan_user(ec_dict):
    ckan_dict = {}

    for ckan_name, ec_name in ckan_to_ec_user_mapping.iteritems():
        if ec_dict.get(ec_name):
            ckan_dict[ckan_name] = ec_dict.get(ec_name)

    return ckan_dict

def create_package_schema():
    schema = default_create_package_schema()

    _modify_schema(schema)

    schema['name'].append(no_pending_dataset_with_same_name)

    schema['title'].extend([
        unique_title_within_organization,
        no_pending_dataset_with_same_title_in_same_org,
    ])

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


def ec_create_user_schema():
    boolean_validator = get_validator('boolean_validator')
    return {
        'UserName': [not_empty, unicode],
        'Password': [not_empty, unicode],
        'IsRegisteredUser': [not_empty, boolean_validator],
        'Email': [not_empty, unicode],
        'FirstName': [not_empty, unicode],
        'LastName': [not_empty, unicode],
        'DisplayName': [not_empty, unicode],
        'About': [ignore_missing, unicode],
        'OrganisationId': [ignore_missing, unicode],
    }


def update_package_schema():
    schema = default_update_package_schema()

    _modify_schema(schema)
    name_validator = get_validator('name_validator')
    schema['name'] = [not_empty, unicode, trim_string(100), name_validator,
                      no_pending_dataset_with_same_name]

    return schema


def _modify_schema(schema):

    name_validator = get_validator('name_validator')
    not_missing = get_validator('not_missing')
    ignore_empty = get_validator('ignore_empty')
    not_empty = get_validator('not_empty')
    boolean_validator = get_validator('boolean_validator')

    convert_to_extras = get_converter('convert_to_extras')

    # Mandatory fields

    schema['__before'] = [tags_max_length(64000)]

    schema['id'] = [ignore_empty, unicode]

    schema['name'] = [not_empty, unicode, trim_string(100), name_validator]

    schema['title'] = [not_empty, string_max_length(255), unicode]

    schema['notes'] = [not_empty, string_max_length(4000), unicode]

    schema['maintainer'] = [not_empty, string_max_length(255), unicode]

    schema['maintainer_email'] = [not_empty, string_max_length(255), unicode]

    schema['license_id'] = [not_empty, unicode]

    schema['openness_rating'] = [not_empty, int_validator, int_range(0, 5),
                                 convert_to_extras]

    schema['quality'] = [not_empty, int_validator, int_range(0, 5),
                         convert_to_extras]

    schema['needs_approval'] = [not_missing, boolean_validator, convert_to_extras]
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

    schema['needs_approval'] = [convert_from_extras]


    return schema


def resource_schema():
    schema = _modify_resource_schema()

    # TODO: Why do we need this?
    schema.update({
#        'package_id': [not_empty, unicode],
        'created':  [ignore_missing, iso_date, unicode],
        'last_modified': [ignore_missing, iso_date, unicode],
        'cache_last_updated': [ignore_missing, iso_date, unicode],
        'webstore_last_updated': [ignore_missing, iso_date, unicode],
    })
    return schema


def custom_resource_extras_schema():

    not_missing = get_validator('not_missing')

    schema = default_extras_schema()

    schema['key'] = [not_empty, string_max_length(255), unicode]
    schema['value'] = [not_missing, string_max_length(64000)]

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

    schema['extras'] = custom_resource_extras_schema()

    # Internal fields

    schema['ec_api_version_id'] = [ignore_missing, unicode]

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


def update_organization_schema():
    boolean_validator = get_validator('boolean_validator')
    not_missing = get_validator('not_missing')
    convert_to_extras = get_converter('convert_to_extras')
    group_name_validator = get_validator('group_name_validator')
    schema = default_update_group_schema()
    schema.update({
        'name': [not_empty, unicode, group_name_validator,
                 no_pending_organization_with_same_name],
        'needs_approval': [not_missing, boolean_validator, convert_to_extras]
    })
    return schema


def user_schema():
    user_name_validator = get_validator('user_name_validator')
    schema = default_user_schema()
    schema['name'] = [not_empty, url_name_validator, user_name_validator, unicode]
    return schema
