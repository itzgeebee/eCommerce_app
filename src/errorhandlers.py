import json

from flask import jsonify, make_response
from src import app
from jsonschema import ValidationError
from werkzeug.exceptions import HTTPException


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "success": False,
        "error": error.description,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description, ValidationError):
        original_error = error.description
        return make_response(jsonify({'success': False,
                                      'error': original_error.message}), 400)
    # handle other "Bad Request"-errors
    return jsonify({"success": False, "error": error.description,
                    "message": "bad request"}), 400


@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({"success": False, "error": error.description,
                    "message": "unauthorized"}), 401


@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({"success": False, "error": error.description,
                    "message": "forbidden"}), 403


@app.errorhandler(405)
def invalid_method_error(error):
    return jsonify({"success": False, "error": error.description,
                    "message": "invalid method"}), 405


@app.errorhandler(422)
def not_processable_error(error):
    return jsonify({"success": False, "error": error.description,
                    "message": "not processable"}), 422


@app.errorhandler(409)
def duplicate_resource_error(error):
    return jsonify({"success": False, "error": error.description,
                    "message": "duplicate resource"}), 409


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"success": False, "error": 500,
                    "message": "internal server error"}), 500

