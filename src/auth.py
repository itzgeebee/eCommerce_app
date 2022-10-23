from flask import (url_for,
                   request,
                   jsonify, g)

from flask_expects_json import expects_json
from .helpers.errors import invalid_token_response
from .models import (Customer, BlacklistToken)
from werkzeug.exceptions import abort
from . import app, db, mail_sender, bcrypt, schema
from .helpers.auth_tokens import (
    encode_auth_token, decode_auth_token,
    check_valid_header
)
from .helpers.transform_user import transform_user_response

from flask_mail import Message
import re

from .schema.defineSchema import auth_schema, login_schema, forgot_password_schema, reset_password_schema, \
    change_password_schema


def validate_mail(address):
    pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    if re.match(pattern, address):
        return True
    return False


def send_email(user):
    tok = user.get_token()
    msg = Message()
    msg.subject = "reset password"
    msg.recipients = [user.mail]
    msg.body = f"follow this link to reset your password " \
               f"https://gadgehaven.herokuapp.com{url_for('verify_reset', token=tok)}"
    mail_sender.send(msg)


@app.route("/api/v1/auth/register/", methods=["POST"])
@expects_json(auth_schema)
def register():

    reg_data = g.data
    first_name = reg_data.get("first_name", None)
    last_name = reg_data.get("last_name", None)
    street = reg_data.get("street", None)
    city = reg_data.get("city", None)
    zip = reg_data.get("zip", None)
    phone = reg_data.get("phone", None)
    mail = reg_data.get("mail", None)
    password = reg_data.get("password", None)
    role = reg_data.get("role", None)
    confirm_password = reg_data.get("confirm_password", None)
    if not validate_mail(mail):
        app.logger.error('bad email format')
        abort(400, "bad email format")

    if password != confirm_password:
        app.logger.error("passwords do not match")
        abort(400, "passwords do not match")

    new_user = Customer(mail=mail,
                        password=bcrypt.generate_password_hash(
                            password, 12).decode('utf-8'),
                        first_name=first_name,
                        last_name=last_name,
                        street=street,
                        city=city,
                        zip=zip,
                        phone=phone,
                        role=role
                        )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422, e.args[0])
    else:
        auth_token = encode_auth_token(new_user.id)
        return jsonify({
            "success": True,
            "data": {
                "auth_token": auth_token,
                "user": transform_user_response(new_user)
            }
        }), 201  # created


@app.route('/api/v1/auth/login/', methods=["POST"])
@expects_json(login_schema)
def login():
    login_data = g.data
    user_email = login_data.get("mail", None)
    user_password = login_data.get("password", None)
    if not validate_mail(user_email):
        app.logger.error('bad email format')
        abort(400, "bad email format")
    user = Customer.query.filter_by(mail=user_email).first()
    if not user:
        app.logger.error('User not found')
        abort(404, "invalid password or email")

    if not bcrypt.check_password_hash(user.password, user_password):
        abort(401, "invalid password or email")
    auth_token = encode_auth_token(user.id)
    return jsonify({
        "success": True,
        "data": {
            "auth_token": auth_token,
            "user": transform_user_response(user)
        }
    }), 200


@app.route("/api/v1/auth/forgot-password/", methods=["POST"])
@expects_json(forgot_password_schema)
def forgot_password():
    request_data = g.data
    mail = request_data.get("mail", None)

    if not validate_mail(mail):
        app.logger.error('bad email format')
        abort(400, "bad email format")

    user = Customer.query.filter_by(mail=mail).first()
    if not user:
        app.logger.error('User not found')
        abort(404, "User not found")
    try:
        send_email(user)
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        return jsonify({
            "success": True,
            "message": "link sent to mail",
            "mail": mail,
        })


@app.route("/api/v1/auth/reset-password/<int:user_id>/", methods=["PATCH"])
@expects_json(change_password_schema)
def password_reset(user_id):
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    decoded_token = decode_auth_token(resp)

    if not resp:
        return invalid_token_response()
    if decoded_token != user_id:
        return invalid_token_response()

    request_data = g.data
    old_password = request_data.get("old_password", None)
    new_password = request_data.get("new_password", None)
    confirm_password = request_data.get("confirm_password", None)
    if len(new_password) < 6:
        app.logger.error('password too short')
        abort(400, "password too short")

    if old_password == new_password:
        app.logger.error('new password same as old password')
        abort(400, "new password same as old password")
    if new_password != confirm_password:
        abort(400, "passwords do not match")
    user = Customer.query.get(user_id)
    if not user:
        app.logger.error('User not found')
        abort(404, "User not found")

    if not bcrypt.check_password_hash(pw_hash=user.password, password=old_password):
        app.logger.error('invalid password')
        abort(400, "invalid password")

    user.password = bcrypt.generate_password_hash(
        new_password, 12).decode('utf-8')
    blacklisted_token = BlacklistToken(token=resp)
    db.session.add(blacklisted_token)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        return jsonify({
            "success": True,
            "message": "password changed",
            "auth_token": encode_auth_token(user.id),
            "data": {
                "user": transform_user_response(user)
            }
        })


@app.route("/api/v1/auth/reset-password/<token>/", methods=["POST"])
@expects_json(reset_password_schema)
def verify_reset(token):
    request_data = g.data
    new_password = request_data.get("new_password")
    confirm_password = request_data.get("confirm_password")
    if len(new_password) < 6:
        app.logger.error('password too short')
        abort(400, "password too short")

    if new_password != confirm_password:
        abort(400, "passwords do not match")

    user = Customer.verify_token(token)
    if user is None:
        app.logger.error('user not found')
        abort(401, "user not found")

    user.password = bcrypt.generate_password_hash(
        new_password, 12).decode('utf-8')
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422, e.args[0])
    else:
        auth_token = encode_auth_token(user.id)
        return jsonify({
            "success": True,
            "data": {
                "auth_token": auth_token,
                "user": transform_user_response(user)
            }
        })


@app.route('/api/v1/auth/logout/')
def logout():
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    if not resp:
        return invalid_token_response()
    blacklist_token = BlacklistToken(token=resp)

    try:
        db.session.add(blacklist_token)
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        if e.args[0].startswith("(psycopg2.errors.UniqueViolation)"):
            return jsonify({
                "success": True,
                "message": "already logged out"
            })
        abort(500)
    else:
        return jsonify({
            "success": True,
            "message": "successfully logged out"
        })


