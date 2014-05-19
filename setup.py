from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(
    name='ckanext-glasgow',
    version=version,
    description="CKAN extension for the Glasgow Open Data Portal",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='http://data.glasgow.gov.uk',
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
        glasgow=ckanext.glasgow.plugins:GlasgowPlugin
    ''',
)
