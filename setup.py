from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name='ckanext-glasgow',
    version=version,
    description="CKAN extension for the Glasgow TSB Future Cities Portal",
    long_description='''
    ''',
    classifiers=[],
    keywords='',
    author='Open Knowledge',
    author_email='info@ckan.org',
    url='https://github.com/okfn/ckanext-glasgow',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.glasgow'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
    [ckan.plugins]
    # Add plugins here, e.g.
    glasgow_schema=ckanext.glasgow.plugins:GlasgowSchemaPlugin
    glasgow_harvest=ckanext.glasgow.plugins:CustomHarvestPlugin
    ec_initial_harvester=ckanext.glasgow.harvesters.ec_harvester:EcInitialHarvester
    ec_changelog_harvester=ckanext.glasgow.harvesters.changelog:EcChangelogHarvester
    create_users=ckanext.glasgow.plugins:CreateUsersPagePlugin

    [paste.paster_command]
    changelog_update=ckanext.glasgow.commands.changelog_update:UpdateFromEcApiChangeLog
    ''',
)
