import socket
from threading import Thread

from pylons import config

from ckanext.glasgow.tests.mock_ec import run as run_mock_ec_server


def run_mock_ec(port=7071):

    # Check if alredy running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex(('0.0.0.0', port))
    s.close()
    if(result == 111):

        def run():
            run_mock_ec_server(port=port, debug=False)

        t = Thread(target=run)
        t.daemon = True
        t.start()

        config['ckanext.glasgow.data_collection_api'] = 'http://0.0.0.0:{0}'.format(port)
        config['ckanext.glasgow.metadata_api'] = 'http://0.0.0.0:{0}'.format(port)
