ckanext-glasgow
===============

[![Build Status](https://travis-ci.org/okfn/ckanext-glasgow.svg?branch=master)](https://travis-ci.org/okfn/ckanext-glasgow)

CKAN Extensions specific to Open Glasgow


## Configuration options

    ## Authorization Settings

    ckan.auth.anon_create_dataset = false
    ckan.auth.create_unowned_dataset = false
    ckan.auth.create_dataset_if_not_in_organization = false
    ckan.auth.user_create_groups = true
    ckan.auth.user_create_organizations = true
    ckan.auth.user_delete_groups = true
    ckan.auth.user_delete_organizations = true
    ckan.auth.create_user_via_api = false
    ckan.auth.create_user_via_web = true
    ckan.auth.roles_that_cascade_to_sub_groups = admin


    ## Search Settings

    ckan.site_id = glasgow


    ## Plugins Settings

    ckan.plugins = stats text_preview recline_preview glasgow_schema ec_initial_harvester oauth2waad

    # Local mock API
    #ckanext.glasgow.data_collection_api=http://localhost:7070
    #ckanext.glasgow.metadata_api=http://localhost:7070
    ckanext.glasgow.data_collection_api=http://gccctpecdatacollectionservicesint.cloudapp.net:8080
    ckanext.glasgow.metadata_api=http://gccctpecmetadataservicesint.cloudapp.net:8081

    # Only if auth is not in place
    ckanext.glasgow.tmp_auth_token_file=/home/okfn/tmp_auth_token.txt

    # OAuth 2.0 WAAD settings
    ckanext.oauth2waad.client_id = ...
    # Change to relevant server
    ckanext.oauth2waad.redirect_uri = https://localhost:5000/_waad_redirect_uri
    ckanext.oauth2waad.auth_endpoint = https://login.windows.net/common/oauth2/authorize
    ckanext.oauth2waad.auth_token_endpoint = https://login.windows.net/common/oauth2/token
    ckanext.oauth2waad.resource = http://GCCCTPECServicesINT.cloudapp.net:8080/
    ckanext.oauth2waad.csrf_secret = ...

    ## Storage Settings

    ckan.storage_path = ...
