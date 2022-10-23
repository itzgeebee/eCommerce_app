from flask import (request, jsonify, session, g)
from flask_expects_json import expects_json

from src.models import Product
from werkzeug.exceptions import abort
from src import app
from flask_login import current_user

from src.schema.defineSchema import add_to_cart_schema, update_cart_schema


@app.route("/api/v1/cart/", methods=['POST'])
@expects_json(add_to_cart_schema)
def add_to_cart():

    request_data = g.data
    product_id = request_data.get("prod_id", None)
    quantity = request_data.get("qty", None)
    if not product_id or not quantity:
        abort(400, "Missing product id or quantity")

    # check for ids and quantity in session
    # flask session can only hold two variables,
    # so a dictionary is passed into it to hold as many variables necessary
    # dictionary structure: {product_id:quantity}
    if "cart_dict" not in session:
        session["cart_dict"] = {}
    cart_dict = session["cart_dict"]
    if product_id in cart_dict:
        cart_dict[product_id] += quantity
    else:
        cart_dict[product_id] = quantity
    session["cart_dict"] = cart_dict

    return jsonify({"success": True,
                    "message": "Product added to cart",
                    "data": {
                        "products": cart_dict
                    }}), 201


@app.route("/api/v1/cart/<int:prod_id>/", methods=['PATCH'])
@expects_json(update_cart_schema)
def change_cart_quantity(prod_id):
    request_data = g.data
    quantity = request_data.get("qty", None)
    if not quantity:
        abort(400, "Missing quantity")

    cart_dict = session["cart_dict"]
    if prod_id not in cart_dict:
        abort(404, "Product not in cart")

    cart_dict[prod_id] = quantity
    session["cart_dict"] = cart_dict
    return jsonify({"success": True,
                    "data": {
                        "products": cart_dict,
                        "product_id": prod_id
                    },
                    "message": "Product quantity updated"})



@app.route('/api/v1/cart/')
def get_cart():
    try:
        cart_dict = session["cart_dict"]
    except KeyError:
        abort(404, description="key not found")
    else:
        cart_prods = []
        calculator_list = []
        print(cart_dict)
        for prod_id, qty in cart_dict.items():
            prd = Product.query.get(prod_id)
            if not prd: # check if product exists
                abort(404, f"Product with id: {prod_id} not found")
            cart_product = {"prod": prd.to_dict(), "qty": qty}
            price = prd.price * qty
            calculator_list.append(price)
            cart_prods.append(cart_product)
        total = sum(calculator_list)

        cart_json = jsonify({
            "data": {
                "products": cart_prods,
                "total_price": total
            },
            "success": True,
        })

        return cart_json


@app.route("/api/v1/cart/<int:prod_id>/", methods=["DELETE"])
def remove_from_cart(prod_id):
    prod = prod_id
    cart_dict = session["cart_dict"]
    if prod not in cart_dict:
        return jsonify({
            "success": True,
            "data": {
                "product_id": prod_id,
                "products": cart_dict
            },
            "message": "Product removed from cart"
        })
    try:
        cart_dict.pop(prod)
        session["cart_dict"] = cart_dict
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        return jsonify({
            "success": True,
            "data": {
                "product_id": prod_id,
                "products": cart_dict
            },
            "message": "Product removed from cart"
        })


@app.route("/api/v1/cart/clear/", methods=["DELETE"])
def clear_cart():
    if "cart_dict" not in session:
        return jsonify({
            "success": True,
            "message": "cart cleared"
        }), 204
    session["cart_dict"].clear()

    return jsonify({
        "success": True,
        "message": "cart cleared"
    }), 204
