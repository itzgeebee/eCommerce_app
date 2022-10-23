from flask import (url_for,
                   request,
                   jsonify, g)
from flask_expects_json import expects_json

from src.auth import validate_mail
from src.helpers.errors import invalid_token_response
from src.helpers.auth_tokens import check_valid_header, decode_auth_token
from src.helpers.transform_user import transform_user_response
from src.models import (Customer, Product,
                        Order, OrderDetails,
                        )
from werkzeug.exceptions import abort
from src import app, db
from src.schema.defineSchema import update_user_schema


@app.route('/api/v1/user/<int:user_id>/account/')
def get_user_account(user_id):
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    decoded_token = decode_auth_token(resp)
    if not resp:
        return invalid_token_response()
    if decoded_token != user_id:
        return invalid_token_response()
    customer = Customer.query.get(user_id)
    if not customer:
        abort(404)
    customer_dict = transform_user_response(customer)
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
            "data": {
                "user": customer_dict,
                "user_orders": orders,
            }
        })


@app.route('/api/v1/user/<int:user_id>/')
def get_user_details(user_id):
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    decoded_token = decode_auth_token(resp)
    if not resp:
        return invalid_token_response()
    if decoded_token != user_id:
        return invalid_token_response()
    customer = Customer.query.get(user_id)
    if not customer:
        abort(404)

    customer_dict = transform_user_response(customer)

    return jsonify({
        "success": True,
        "data":
            {
                "user": customer_dict
            }
        })



@app.route('/api/v1/user/<int:user_id>/', methods=['PATCH'])
@expects_json(update_user_schema)
def edit_profile(user_id):
    fields_to_include = ['first_name', 'last_name', 'mail', 'password',
              'phone', 'city', 'state', 'zip']

    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    decoded_token = decode_auth_token(resp)
    if not resp:
        return invalid_token_response()
    if decoded_token != user_id:
        return invalid_token_response()

    request_data = g.data
    sanitized_data = {k: v for k, v in request_data.items()
                      if k in fields_to_include}


    customer = Customer.query.get(user_id)

    if not customer:
        abort(404, "User not found")

    if sanitized_data.get("mail", None):
        if not validate_mail(sanitized_data.get("mail", None)):
            abort(400, "Invalid email address")

    if request_data == {}:
        abort(400, "Please provide a valid field to update")

    for key, value in sanitized_data.items():
        setattr(customer, key, value)

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:
        return jsonify({
            "success": True,
            "message": "user updated",
            "data": {
                "user": transform_user_response(customer)
            }
        })

@app.route('/api/v1/user/<int:user_id>/', methods=['DELETE'])
def delete_profile(user_id):
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    decoded_token = decode_auth_token(resp)
    if not resp:
        return invalid_token_response()
    if decoded_token != user_id:
        return invalid_token_response()
    customer = Customer.query.get(user_id)
    if not customer:
        return jsonify({
            "success": True,
            "message": "user does not exist"
        })
    db.session.delete(customer)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        return jsonify({
            "success": True,
            "user_id": user_id
        })

