import logging
import uuid
import json

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

    return handle_dataset_request()


@app.route('/Datasets', methods=['PUT'])
def request_dataset_update():

    return handle_dataset_request()


@app.route('/Files', methods=['POST'])
def request_file_create():

    return handle_file_request()


@app.route('/Files', methods=['PUT'])
def request_file_update():

    return handle_file_request()

@app.route('/Organisations/<int:org_id>/Datasets', methods=['GET'])
def request_datasets(org_id):
    skip = int(flask.request.args.get('$skip', 0))
    metadata_result_set = {
        1: [],
        2: [],
        4: [
            {
                "Id": 3,
                "Metadata": {
                    "Category": "debitis",
                    "Description": "Sint perspiciatis et dolorem. Consectetur impedit porro omnis nisi adipisci eum rerum tenetur. Voluptate accusamus praesentium autem molestiae possimus a quibusdam harum.",
                    "License": "http://mayert.us/gibsondickinson/dicki.html",
                    "MaintainerContact": "nova_windler@swift.uk",
                    "MaintainerName": "Marge Conn",
                    "OpennessRating": "0",
                    "PublishedOnBehalfOf": "Ms. Gloria Bode",
                    "Quality": "3",
                    "StandardName": "Iste maxime ad non ea",
                    "StandardRating": "4",
                    "StandardVersion": "4.4.0",
                    "Tags": "beatae consequatur sunt ducimus mollitia",
                    "Title": "Raj Data Set 001",
                    "Theme": "assumenda",
                    "UsageGuidance": "Sed magnam labore voluptatem accusamus aut dicta eos et. Et omnis aliquam fugit sed iusto. Consectetur esse et tempora."
                    },
                "CreatedTime": "2014-06-09T14:08:08.78",
                "ModifiedTime": "2014-06-09T14:08:08.78",
                "OrganisationId": 4,
                "Title": "Raj Data Set 001"
                },
            {
                "Id": 7,
                "Metadata": {
                    "Category": "quia",
                    "Description": "Eos porro labore vero. Ex voluptas dolore id repellat. Dolorum animi maiores debitis nesciunt maiores fuga.",
                    "License": "http://watsicaoconnell.info/rosenbaum/auer.html",
                    "MaintainerContact": "sandra@friesenborer.ca",
                    "MaintainerName": "Liana Pouros",
                    "OpennessRating": "4",
                    "PublishedOnBehalfOf": "Katlyn Friesen",
                    "Quality": "3",
                    "StandardName": "Et deleniti saepe libero quasi eos et nobis",
                    "StandardRating": "1",
                    "StandardVersion": "4.0.78",
                    "Tags": "deleniti rerum ratione in nemo",
                    "Title": "Dolorum qui illo aliquid",
                    "Theme": "illum",
                    "UsageGuidance": "Eveniet consequatur recusandae omnis distinctio aspernatur. Numquam sit nam dolorum rerum aliquid commodi. Excepturi sit enim dolorem ipsa possimus omnis. Perspiciatis qui delectus id modi sunt aut consectetur. Repellat suscipit ipsum est."
                    },
                "CreatedTime": "2014-06-09T21:46:48.51",
                "ModifiedTime": "2014-06-09T21:46:48.51",
                "OrganisationId": 4,
                "Title": "Dolorum qui illo aliquid"
                },
            {
                "Id": 8,
                "Metadata": {
                    "Category": "sit",
                    "Description": "Fuga voluptas ut et modi est maiores rerum. Sint qui aspernatur inventore quibusdam vel nulla temporibus necessitatibus. Vel voluptas similique quo illo. Repellendus totam ab repudiandae. Enim in corrupti illo ea reprehenderit dicta.",
                    "License": "http://schambergermills.us/schowalter/champlin.html",
                    "MaintainerContact": "granville.collins@hessel.co.uk",
                    "MaintainerName": "Rolando Kemmer",
                    "OpennessRating": "0",
                    "PublishedOnBehalfOf": "Wayne Greenfelder",
                    "Quality": "1",
                    "StandardName": "Est alias qui doloribus possimus iusto",
                    "StandardRating": "0",
                    "StandardVersion": "5.5.44",
                    "Tags": "possimus nemo id laboriosam expedita",
                    "Title": "Non ipsum dolore voluptatem",
                    "Theme": "sint",
                    "UsageGuidance": "Ut suscipit labore excepturi ex laudantium ex voluptates. Sed accusantium sed consequuntur sequi ipsa modi. Delectus perspiciatis mollitia sint ullam maxime et et omnis. Sint ipsa quia a nesciunt."
                    },
                "CreatedTime": "2014-06-09T21:46:52.52",
                "ModifiedTime": "2014-06-09T21:46:52.52",
                "OrganisationId": 4,
                "Title": "Non ipsum dolore voluptatem"
                }
            ],
        }
    res = metadata_result_set.get(org_id, [])
    return flask.jsonify(**{
        "MetadataResultSet": res[skip:],
        "ErrorMessage": None,
        "IsErrorResponse": False,
        "IsRetryRequested": False
        }
    )


@app.route('/Metadata/Organisation', methods=['GET'])
def request_orgs():
    skip = int(flask.request.args.get('$skip', 0))
    metadata_result_set = [
        {
            "Id": 1,
            "Title": "Glasgow City Council",
            "CreatedTime": "2014-05-21T06:06:18.353",
            "ModifiedTime": "2014-05-21T06:06:18.353"
            },
        {
            "Id": 2,
            "Title": "Microsoft",
            "CreatedTime": "2014-05-21T00:00:00",
            "ModifiedTime": "2014-05-21T00:00:00"
            },
        {
            "Id": 4,
            "Title": "Test Org",
            "CreatedTime": "2014-05-22T00:06:18",
            "ModifiedTime": "2014-05-22T06:06:18"
            }
        ]

    return flask.jsonify(**{
        "MetadataResultSet": metadata_result_set[skip:],
        "ErrorMessage": None,
        "IsErrorResponse": False,
        "IsRetryRequested": False
        }
    )


def handle_dataset_request():
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
       flask.request.headers['Authorization'] == 'Bearer unknown_token'):
        response = flask.jsonify(
            Message='Not Auhtorized'
        )
        response.status_code = 401
        return response

    # Basic Validation

    for field in dataset_mandatory_fields:
        if not data.get(field):
            response = flask.jsonify(
                Message='Missing fields',
                ModelState={
                    'model.' + field:
                    ["The {0} field is required.".format(field)]
                })
            response.status_code = 400
            return response

    for field in dataset_fields_under_255_characters:
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


def handle_file_request():

    if app.debug:
        app.logger.debug('Headers received:\n{0}'
                         .format(flask.request.headers))

    # Authorization

    if ('Authorization' not in flask.request.headers or
       flask.request.headers['Authorization'] == 'unknown_token'):
        response = flask.jsonify(
            Message='Not Auhtorized'
        )
        response.status_code = 401
        return response

    # Check for files
    if not len(flask.request.files):
        response = flask.jsonify(
            # TODO: use actual message
            Message='File Missing'
        )
        response.status_code = 400
        return response

    uploaded_file = flask.request.files.values()[0]
    if app.debug:
        app.logger.debug('File headers received:\n{0}'
                         .format(uploaded_file.headers))

    file_name = uploaded_file.filename

    if not len(flask.request.form):
        response = flask.jsonify(
            # TODO: use actual message
            Message='Metadata Missing'
        )
        response.status_code = 400
        return response

    metadata_fields = flask.request.form.values()[0]

    try:
        metadata = json.loads(metadata_fields)
    except ValueError:
        response = flask.jsonify(
            # TODO: use actual message
            Message='Wrong File Metadata'
        )
        response.status_code = 400
        return response
    if app.debug:
        app.logger.debug('File metadata received:\n{0}'
                         .format(metadata))

    for field in file_mandatory_fields:
        if not metadata.get(field):
            response = flask.jsonify(
                Message='Missing fields',
                ModelState={
                    'model.' + field:
                    ["The {0} field is required.".format(field)]
                })
            response.status_code = 400
            return response

    for field in file_fields_under_255_characters:
        if metadata.get(field) and len(metadata.get(field, '')) > 255:
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
        'Request dataset creation': 'POST /Datasets',
        'Request dataset update': 'PUT /Datasets',
        'Request file creation': 'POST /Files',
        'Request file update': 'PUT /Files',

    }

    return flask.jsonify(**api_desc)


def run(**kwargs):
    app.run(**kwargs)


if __name__ == '__main__':
    run(port=7070, debug=True)
