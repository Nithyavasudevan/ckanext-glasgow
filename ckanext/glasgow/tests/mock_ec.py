import logging
import uuid

import flask
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException


def make_json_app(import_name, **kwargs):
    """
    Creates a JSON-oriented Flask app.

    All error responses that you don't specifically
    manage yourself will have application/json content
    type, and will contain JSON like this (just an example):

    { "message": "405: Method Not Allowed" }
    """
    def make_json_error(ex):
        response = flask.jsonify(Message=str(ex))
        response.status_code = (ex.code
                                if isinstance(ex, HTTPException)
                                else 500)
        return response

    app = flask.Flask(import_name, **kwargs)

    for code in default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = make_json_error

    # Add logging
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    return app

app = make_json_app(__name__)

dataset_all_fields = [
    'Category',
    'Description',
    'License',
    'MaintainerContact',
    'MaintainerName',
    'OpennessRating',
    'PublishedOnBehalfOf',
    'Quality',
    'StandardName',
    'StandardRating',
    'StandardVersion',
    'Tags',
    'Theme',
    'Title',
    'UsageGuidance',
]

dataset_mandatory_fields = [

    'Title',
    'Description',
    'MaintainerName',
    'MaintainerContact',
    'License',
    'OpennessRating',
    'Quality',
]

dataset_fields_under_255_characters = [
    'Title',
    'MaintainerName',
    'MaintainerContact',
    'License',
    'Category',
    'PublishedOnBehalfOf',
    'StandardName',
    'StandardVersion',
    'Theme',
    'UsageGuidance',
]

file_all_fields = [
    'DatasetId',
    'Title',
    'Description',
    'Type',
    'License',
    'OpennessRating',
    'Quality',
    'StandardName',
    'StandardRating',
    'StandardVersion',
    'CreationDate',
]

file_mandatory_fields = [
    'DatasetId',
    'Title',
    'Description',
    'Type',
]

file_fields_under_255_characters = [
    'Title',
    'Type',
    'License',
    'StandardName',
    'StandardVersion',
]


@app.route('/Datasets', methods=['POST'])
def request_dataset_create():

    return handle_request('dataset')


@app.route('/Datasets', methods=['PUT'])
def request_dataset_update():

    return handle_request('dataset')


@app.route('/Files', methods=['POST'])
def request_file_create():

    return handle_request('file')


@app.route('/Files', methods=['PUT'])
def request_file_update():

    return handle_request('file')


def handle_request(request_type='dataset'):
    data = flask.request.json

    if app.debug:
        app.logger.debug('Headers received:\n{0}'
                         .format(flask.request.headers))
        app.logger.debug('Data received:\n{0}'.format(data))

    if not data:
        response = flask.jsonify(
            Message='No data received'
        )
        response.status_code = 400
        return response

    # Authorization

    if ('Authorization' not in flask.request.headers or
       flask.request.headers['Authorization'] == 'unknown_token'):
        response = flask.jsonify(
            Message='Not Auhtorized'
        )
        response.status_code = 401
        return response

    # Basic Validation

    if request_type == 'dataset':
        mandatory_fields = dataset_mandatory_fields
        fields_under_255_characters = dataset_fields_under_255_characters
    elif request_type == 'file':
        mandatory_fields = file_mandatory_fields
        fields_under_255_characters = file_fields_under_255_characters

    for field in mandatory_fields:
        if not data.get(field):
            response = flask.jsonify(
                Message='Missing fields',
                ModelState={
                    'model.' + field:
                    ["The {0} field is required.".format(field)]
                })
            response.status_code = 400
            return response

    for field in fields_under_255_characters:
        if data.get(field) and len(data.get(field, '')) > 255:
            response = flask.jsonify(
                Message='Field too long',
                ModelState={
                    'model.' + field:
                    ["{0} field must be shorter than 255 characters."
                     .format(field)]
                })
            response.status_code = 400
            return response

    # All good, return a request id
    request_id = unicode(uuid.uuid4())
    if app.debug:
        app.logger.debug('Request id generated:\n{0}'.format(request_id))

    return flask.jsonify(
        RequestId=request_id
    )


@app.route('/')
def api_description():

    api_desc = {
        'Request dataset creation': 'POST /datasets',
        'Request dataset update': 'PUT /datasets',
    }

    return flask.jsonify(**api_desc)


def run(**kwargs):
    app.run(**kwargs)


if __name__ == '__main__':
    run(port=7070, debug=True)
