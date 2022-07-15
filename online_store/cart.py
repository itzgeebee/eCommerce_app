from flask import (request,jsonify, session)
from online_store.models import Product
from werkzeug.exceptions import abort
from online_store import app
from flask_login import current_user


@app.route("/cart", methods=['POST'])
def add_to_cart():
    try:
        request_data = request.get_json()
        product_id = request_data.get("prod_id", None)
        quantity = request_data.get("qty", None)
    except Exception as e:
        app.logger.error(e)
        abort(400)
    else:
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
                        "logged_in": current_user.is_authenticated,
                        "products": cart_dict})


@app.route("/cart", methods=['PATCH'])
def change_cart_quantity():
    try:
        request_data = request.get_json()
        product_id = request_data.get("prod_id", None)
        quantity = request_data.get("qty", None)
    except Exception as e:
        app.logger.error(e)
        abort(400)
    else:
        cart_dict = session["cart_dict"]
        if product_id not in cart_dict:
            return jsonify({
                "success": False,
                "message": "product id not found in cart"
            }), 404
        cart_dict[product_id] = quantity
        session["cart_dict"] = cart_dict
        return jsonify({"success": True,
                        "logged_in": current_user.is_authenticated,
                        "product_id": product_id})


@app.route('/cart')
def get_cart():
    try:
        cart_dict = session["cart_dict"]
    except KeyError:
        abort(404, description="key not found")
    else:

        cart_prods = []
        calculator_list = []

        for prod in cart_dict:
            prd = Product.query.get(prod)
            qty = cart_dict[prod]
            cart_product = {"prod": prd.to_dict(), "qty": qty}
            price = prd.price * qty
            calculator_list.append(price)
            cart_prods.append(cart_product)
        total = sum(calculator_list)

        cart_json = jsonify({
            "products": cart_prods,
            "total_price": total,
            "success": True,
            "logged_in": current_user.is_authenticated,
        })

        return cart_json


@app.route("/cart/<int:prodId>", methods=["DELETE"])
def remove_from_cart(prodId):
    prod = prodId
    cart_dict = session["cart_dict"]
    if prod not in cart_dict:
        abort(404)
    try:
        cart_dict.pop(prod)
        session["cart_dict"] = cart_dict
    except Exception as e:
        app.logger.error(e)
        abort(400)
    else:
        return jsonify({
            "success": True,
            "product_id": prodId,
            "products": cart_dict,
        })

@app.route("/cart/clear", methods=["DELETE"])
def clear_cart():
    if "cart_dict" not in session:
        abort(404)
    session["cart_dict"].clear()

    return jsonify({
        "success":True,
        "logged_in": current_user.is_authenticated,
    })





























