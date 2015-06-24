import unittest
from flask import Flask
from flask_validate import validate, validated, ValidationException


basic_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Basic demo",
    "type": "object",
    "required": ["a"]
}


definitions = {
    "email": {
        "description": "email address",
        "type": "string",
        "format": "email",
        "pattern": "^[0-9a-zA-Z][-+\.0-9a-zA-Z]*@[a-zA-Z0-9-.]*\.[a-zA-Z]{2,9}$",
    },
    "date": {
        "format": "date",
        "type": "string",
        "pattern": "^\d{4}-\d{2}-\d{2}$"
    }
}

signup_schema = {
    "definitions": definitions,
    "type": "object",
    "properties": {
        "email": {
            "$ref": "#/definitions/email",
        },
        "date": {
            "$ref": "#/definitions/date",

        }
    },
    "additionalProperties": False,
}

test_app = Flask(__name__)


@test_app.errorhandler(ValidationException)
def render_pretty_validation_error(e):
    msg = "Validation Errors: %s" % ",".join([str(p) for p in e.errors])
    return msg, 400


@test_app.route('/', methods=['GET', 'POST'])
@validate(basic_schema)
def hello_world():
    return 'Hello World!'


@test_app.route('/a', methods=['GET', 'POST'])
@validate(signup_schema)
def fancy_schema():
    return 'Hello World!'


@test_app.route('/unpack_email', methods=['POST'])
@validate(signup_schema)
def unpack_email():
    return validated.get('email')


class SchemaValidatorTestCase(unittest.TestCase):
    def setUp(self):
        self.app = test_app.test_client()

    def test_fancy(self):
        rv = self.app.post('/a', data='{"email":"cda@cda.im"}', content_type='application/json')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.post('/a', data='{"date":"2012-12-12"}', content_type='application/json')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.post('/a', data='{"date":"1/2/3"}', content_type='application/json')
        self.assertEqual(rv.status_code, 400)

        rv = self.app.post('/a', data='{"email":"cda@x"}', content_type='application/json')
        self.assertEqual(rv.status_code, 400)

        rv = self.app.post('/a', data='{"email":"cda@cda.im", "foo": 1}',
                           content_type='application/json')
        self.assertEqual(rv.status_code, 400)

    def test_basic(self):
        rv = self.app.post('/', data='{"a":"b"}', content_type='application/json')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.post('/', data='{}', content_type='application/json')
        self.assertEqual(rv.status_code, 400)

        rv = self.app.post('/', data='}', content_type='application/json')
        self.assertEqual(rv.status_code, 400)

    def test_validated(self):
        rv = self.app.post('/unpack_email', data='{"email":"a@b.cd"}', content_type='application/json')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual("a@b.cd", rv.data.decode())

        rv = self.app.post('/unpack_email', data='', content_type='application/json')
        self.assertEqual(rv.status_code, 400)
