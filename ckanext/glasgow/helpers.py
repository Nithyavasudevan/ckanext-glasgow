from ckan import model


def get_licenses():

    return [('', '')] + model.Package.get_license_options()


def get_ec_api_id_from_audit(audit_dict):
    object_type = audit_dict.get('ObjectType')
    custom_properties = audit_dict.get('CustomProperties', [])
    if len(custom_properties):
        custom_properties = custom_properties[0]

    object_id = None
    if object_type == 'Dataset':
        object_id = custom_properties.get('DatasetId')
    elif object_type == 'File':
        # TODO: maybe we need VersionId
        object_id = custom_properties.get('FileId')
    if object_type == 'Organisation':
        object_id = custom_properties.get('OrganisationId')

    return object_id
