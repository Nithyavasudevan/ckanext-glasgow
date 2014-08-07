import requests
import ckanext.glasgow.exceptions as exc

def _fetch_from_ec(request):
    if request.status_code != requests.codes.ok:
        raise exc.EcApiException(
            'Unable to get content for URL: {0}:'.format(request.url))

    try:
        result = request.json()
    except ValueError:
        raise exc.EcApiException('Not a JSON response: {0}:'.format(request.url))

    return result


def call_ec_api(endpoint, **kwargs):
    skip = 0

    while True:
        request = requests.get(endpoint, params={'$skip': skip}, verify=False, **kwargs)
        result = _fetch_from_ec(request)

        if not result:
            raise StopIteration

        for i in result:
            yield i

        skip += len(result)
