import slugify

from ckan import plugins as p

from ckanext.harvest.harvesters.base import HarvesterBase


class EcHarvester(HarvesterBase):

    _user_name = None

    def _get_object_extra(self, harvest_object, key):
        '''
        Helper function for retrieving the value from a harvest object extra,
        given the key
        '''
        for extra in harvest_object.extras:
            if extra.key == key:
                return extra.value
        return None

    def _get_site_user(self):
        return p.toolkit.get_action('get_site_user')(
            {
                'ignore_auth': True,
                'defer_commit': True
            }, {})

    def _get_user_name(self):
        if self._user_name:
            return self._user_name

        user = self._get_site_user()
        self._user_name = user['name']

        return self._user_name

    def _get_dataset_name(self, data_dict):
        org_id = data_dict.get('ec_api_org_id',
                               data_dict.get('owner_org'))

        if org_id:
            name = slugify.slugify(
                '-'.join([data_dict['title'][:95], str(org_id)[:4]])
            )
        else:
            name = slugify.slugify(data_dict['title'])

        return name
