import jsonschema
from functools import wraps
from flask import request, g
from werkzeug.local import LocalProxy


# Validated will hold our validated response.json
validated = LocalProxy(lambda: g.validated)


class ValidationException(ValueError):
    def __init__(self, errors):
        self.errors = errors


def check_schema(schema):
    """Raises an exception if schema is broken."""
    jsonschema.Draft4Validator.check_schema(schema)


def validate(schema):
    """Simple schema validator decorator."""

    check_schema(schema)

    def get_errors(data):
        v = jsonschema.Draft4Validator(schema)
        return sorted(v.iter_errors(data), key=lambda e: e.path)

    def validate_payload(data):
        errors = get_errors(data)
        if len(errors) > 0:
            raise ValidationException(errors)
        return data

    def validate_decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):  # This is the part that gets called at runtime!
            g.validated = validate_payload(request.json)
            return fn(*args, **kwargs)
        return wrapped
    return validate_decorator


def check_schema_data(schema, data):
    """Raises an exception if data does not conform to schema."""
    v = jsonschema.Draft4Validator(schema)
    errors = sorted(v.iter_errors(data), key=lambda e: e.path)
    if len(errors) > 0:
        raise ValidationException(errors)
