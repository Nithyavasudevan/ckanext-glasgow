import ckan.plugins as p


class ChangelogController(p.toolkit.BaseController):

    def index(self):
        data_dict = {}
        for param in ('audit_id', 'top', 'object_type'):
            if p.toolkit.request.params.get(param):
                data_dict[param] = p.toolkit.request.params.get(param)
        try:
            changelog = p.toolkit.get_action('changelog_show')({}, data_dict)

            extra_vars = {
                'changelog': changelog,
            }
            return p.toolkit.render('changelog.html',
                                    extra_vars=extra_vars)

        except p.toolkit.NotAuthorized:
            p.toolkit.abort(401,
                            p.toolkit._('Unauthorized to see the Changelog'))
