from flask import jsonify


def invalid_token_response():
    return jsonify({
        "success": False,
        "message": "invalid token",
        "error": 401
    }), 401

def database_error_response(error):
    if error.startswith("(psycopg2.errors.NotNullViolation)"):
        pass