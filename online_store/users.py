from flask import (render_template,
                   redirect, url_for,
                   request,
                   jsonify)
from online_store.models import (Customer, Product,
                                 Order, OrderDetails,
                                 )
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from online_store import app, db, mail_sender, login_manager
from flask_login import (login_user, login_required,
                         current_user, logout_user)
from online_store.forms import (ChangePassword, CreateUserForm,
                                LoginUserForm, ResetPassword,
                                EditUserForm)
from flask_mail import Message
import re


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

# db.drop_all()
# db.create_all()
@login_manager.user_loader
def load_user(id):
    return Customer.query.get(id)


@app.route("/auth/register", methods=["POST"])
def register():
    reg_data = request.get_json()
    first_name = reg_data.get("first_name", None)
    last_name = reg_data.get("last_name", None)
    street = reg_data.get("street", None)
    city = reg_data.get("city", None)
    zip = reg_data.get("zip", None)
    phone = reg_data.get("phone", None)
    mail = reg_data.get("email", None)
    password = reg_data.get("password", None)
    role = reg_data.get("role", None)
    confirm_password = reg_data.get("confirm_password", None)
    if not validate_mail(mail):
        app.logger.error('bad email format')
        return jsonify({
            "success": False,
            "message": "invalid mail format"
        }), 400
    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "invalid password",
            "error": 400
        }), 400
    if password != confirm_password:
        app.logger.error("passwords do not match")
        return jsonify({
            "success": False,
            "message": "password and confirm password do not match",
            "error": 400
        }), 400
    new_user = Customer(mail=mail,
                        password=generate_password_hash(password,
                                                        method='pbkdf2'':sha256',
                                                        salt_length=8),
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
        return jsonify({
            "success": False,
            "message": "email already exists",
            "error": 422
        }), 422
    else:
        login_user(new_user, remember=True)
        return jsonify({
            "success": True,
            "logged_in": current_user.is_authenticated,
            "user_id": current_user.id
        })


@app.route('/auth/login', methods=["POST"])
def login():
    login_data = request.get_json()
    user_email = login_data.get("email", None)
    user_password = login_data.get("password", None)
    if not validate_mail(user_email):
        return jsonify({
            "success": False,
            "message": "invalid mail format",
            "error": 400
        }), 400
    user = Customer.query.filter_by(mail=user_email).first()
    if not user:
        app.logger.error('User not found')
        return jsonify({
            "success": False,
            "message": "user not found",
            "error": 404
        }), 404

    if not check_password_hash(pwhash=user.password, password=user_password):
        abort(401)
    login_user(user, remember=True)

    return jsonify({
        "success": True,
        "logged_in": current_user.is_authenticated,
        "user_id": current_user.id
    })


@app.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    request_data = request.get_json()
    mail = request_data.get("mail", None)
    if not validate_mail(mail):
        return jsonify({
            "success": False,
            "message": "invalid mail format",
            "error": 400
        }), 400
    user = Customer.query.filter_by(mail=mail).first()
    if not user:
        return jsonify({
            "success": False,
            "message": "user not found",
            "error": 404
        }), 404
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
            "logged_in": current_user.is_authenticated,
        })


@app.route("/auth/reset-password/<int:user_id>", methods=["PUT"])
@login_required
def password_reset(user_id):
    request_data = request.get_json()
    old_password = request_data.get("old_password", None)
    new_password = request_data.get("new_password", None)
    confirm_password = request_data.get("confirm_password", None)
    if len(new_password) < 6:
        return jsonify({
            "success": False,
            "message": "invalid password",
            "error": 400
        }), 400
    if old_password == new_password:
        return jsonify({
            "success": False,
            "message": "old password is the same as new password",
            "error": 400
        }), 400
    if new_password != confirm_password:
        abort(400)
    user = Customer.query.get(user_id)
    if not user:
        return jsonify({
            "success": False,
            "message": "user not found"
        }), 404

    if not check_password_hash(pwhash=user.password, password=old_password):
        return jsonify({
            "success": False,
            "message": "invalid old password",
            "error": 401
        }), 401

    user.password = generate_password_hash(new_password, method='pbkdf2'':sha256', salt_length=8)

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        return jsonify({
            "success": True,
            "logged_in": current_user.is_authenticated,
            "user_id": user_id
        })


@app.route("/auth/reset-password/<token>", methods=["POST"])
def verify_reset(token):
    request_data = request.get_json()
    new_password = request_data.get("new_password")
    confirm_password = request_data.get("confirm_password")
    if len(new_password) < 6:
        return jsonify({
            "success": False,
            "message": "invalid password",
            "error": 400
        }), 400
    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "message": "old password is the same as new password",
            "error": 400
        }), 400
    user = Customer.verify_token(token)
    if user is None:
        return jsonify({"error": 404,
                        "success": False,
                        "message": "invalid or expired token"}), 404

    user.password = generate_password_hash(new_password, method='pbkdf2'':sha256', salt_length=8)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        login_user(user)
        return jsonify({
            "success": True,
            "logged_in": current_user.is_authenticated,
            "user_id": current_user.id
        })


@app.route('/user/<int:user_id>/account')
@login_required
def get_user_account(user_id):
    customer = Customer.query.get(user_id)
    if not customer:
        abort(404)
    customer_dict = {
        "id": user_id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "street": customer.street,
        "city": customer.city,
        "zip": customer.zip,
        "phone": customer.phone,
        "mail": customer.mail,
        "role": customer.role
    }
    try:
        order_table = db.session.query(OrderDetails,
                                       Order, Product).select_from(
            OrderDetails).join(Order).join(Product).with_entities(OrderDetails.order_date,
                                                                  Product.price,
                                                                  Product.product_description,
                                                                  Order.quantity).filter(
            OrderDetails.customer_id == user_id
        ).all()

    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        orders = [{
            "order_date": order.order_date,
            "price": order.price,
            "description": order.product_description,
            "quantity": order.quantity,
        } for order in order_table]

        return jsonify({
            "success": True,
            "user": customer_dict,
            "logged_in": current_user.is_authenticated,
            "user_orders": orders,
        })


@app.route('/user/<int:user_id>')
@login_required
def get_user_details(user_id):
    customer = Customer.query.get(user_id)
    if not customer:
        abort(404)

    customer_dict = {
        "id": user_id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "street": customer.street,
        "city": customer.city,
        "zip": customer.zip,
        "phone": customer.phone,
        "mail": customer.mail,
        "role": customer.role
    }

    return jsonify({
            "user": customer_dict,
            "logged_in": current_user.is_authenticated,
            "success": True
        })



@app.route('/user/<int:user_id>', methods=['PATCH'])
@login_required
def edit_profile(user_id):
    request_data = request.get_json()
    customer = Customer.query.get(user_id)

    if not customer:
        abort(404)
    first_name = request_data.get("first_name", None)
    last_name = request_data.get("last_name", None)
    mail = request_data.get("mail", None)
    phone = request_data.get("phone", None)
    zip = request_data.get("zip", None)
    street = request_data.get("street", None)
    city = request_data.get("city", None)

    if not validate_mail(mail):
        abort(400)

    customer.first_name = first_name
    customer.last_name = last_name
    customer.mail = mail
    customer.phone = phone
    customer.zip = zip
    customer.street = street
    customer.city = city

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:
        return jsonify({
            "success": True,
            "logged_in": current_user.is_authenticated,
            "user_id": customer.id
        })

@app.route('/user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_profile(user_id):
    customer = Customer.query.get(user_id)
    if not customer:
        abort(404)
    db.session.delete(customer)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        return jsonify({
            "success": True,
            "user_id": user_id,
            "logged_in": current_user.is_authenticated
        })

@app.route('/auth/logout')
def logout():
    logout_user()
    return jsonify({
        "success": True,
        "logged_in": current_user.is_authenticated
    })
