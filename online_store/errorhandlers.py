from flask import render_template, jsonify
from online_store import app


@app.errorhandler(404)
def not_found_error(error):

    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({"success": False, "error": 400,
                    "message": "bad request"}), 400


@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({"success": False, "error": 401,
                    "message": "unauthorized"}), 401


@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({"success": False, "error": 403,
                    "message": "forbidden"}), 403

@app.errorhandler(405)
def invalid_method_error(error):
    return jsonify({"success": False, "error": 405,
                    "message": "invalid method"}), 405


@app.errorhandler(422)
def not_processable_error(error):
    return jsonify({"success": False, "error": 422,
                    "message": "not processable"}), 422


@app.errorhandler(409)
def duplicate_resource_error(error):
    return jsonify({"success": False, "error": 409,
                    "message": "duplicate resource"}), 409


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"success": False, "error": 500,
                    "message": "internal server error"}), 500
