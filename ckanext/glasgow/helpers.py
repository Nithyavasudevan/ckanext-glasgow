from ckan import model


def get_licenses():

    return [('', '')] + model.Package.get_license_options()
