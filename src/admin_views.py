import os
import re

from flask import (request, send_file, jsonify, g)
from flask_expects_json import expects_json
from sqlalchemy import asc

from src.helpers.errors import invalid_token_response
from src.helpers.auth_tokens import check_valid_header, decode_auth_token
from src.models import (Customer, Product, Order,
                        Reviews, OrderDetails, Role)
from werkzeug.exceptions import abort
from src import app
from src import db
from functools import wraps
import csv

from src.schema.defineSchema import add_product_schema, update_product_schema, update_role_schema


def is_url(url):
    url_pattern = re.compile(
        r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\(["
        r"^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")

    return bool(url_pattern.match(url))


def required_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            resp = check_valid_header(auth_header)
            if not resp:
                return invalid_token_response()
            decoded_token = decode_auth_token(resp)
            current_user = Customer.query.get(decoded_token)
            role_id = current_user.role
            print(role_id)
            get_role = Role.query.get(role_id)
            get_role = get_role.to_dict()
            if get_role["name"] not in roles:
                return abort(403, description="You do not have access to this page, "
                                              "only admin can access this page")
            return f(*args, **kwargs)

        return decorated_function

    return wrapper


@app.route("/admin", methods=["GET", "POST"])
@required_roles("admin")
def admin_home():
    return jsonify({
        "success": True,
    })


@app.route("/api/v1/admin/inventory/", methods=["GET"])
@required_roles("admin")
def inventory():
    page = request.args.get("page", 1, type=int)
    all_prods = Product.query.order_by(
        Product.quantity.asc()).paginate(
        per_page=100, page=page)

    prod_list = [product.to_dict() for product in all_prods.items]

    return jsonify({
        "success": True,
        "data": {"products": prod_list},
        "pages": all_prods.pages,
        "current_page": all_prods.page,
        "per_page": 100,
    })


@app.route("/api/v1/admin/product/restock/<int:prod_id>/", methods=["PATCH"])
@required_roles("admin")
def restock(prod_id):
    product = Product.query.get(prod_id)
    if not product:
        abort(404, "Product not found")
    product.quantity = 100
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:

        return jsonify({
            "success": True,
            "data": {
                "product": product.to_dict()
            }
        })


@app.route("/api/v1/admin/sales/")
@required_roles("admin")
def sales():
    page = request.args.get("page", 1, type=int)
    all_sales = Order.query.order_by(
        Order.quantity.desc()
    ).paginate(
        per_page=100, page=page)
    sales_list = []
    for i in all_sales.items:
        order_dets = OrderDetails.query.get(i.order_details_id)
        prod = {
            "customer_id": order_dets.customer_id,
            "product_id": i.product_id,
            "quantity": i.quantity,
            "order_date": order_dets.order_date
        }
        sales_list.append(prod)
    return jsonify({
        "success": True,
        "data": {
            "sales": sales_list
        },
        "pages": all_sales.pages,
        "current_page": all_sales.page,
        "per_page": 100,
    })


@app.route("/api/v1/admin/products/", methods=["POST"])
@required_roles("admin")
@expects_json(add_product_schema)
def upload_product():
    request_data = g.data

    if not is_url(request_data.get("img_url")):
        abort(400, "Invalid URL")

    quantity = request_data.get("quantity", None)
    product_name = request_data.get("product_name", None)
    product_description = request_data.get("product_description", None)
    category = request_data.get("category", None)
    price = request_data.get("price", None)
    img_url = request_data.get("img_url", None)

    new_product = Product(
        quantity=quantity,
        product_name=product_name,
        product_description=product_description,
        category=category,
        price=price,
        img_url=img_url
    )
    db.session.add(new_product)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)

    return jsonify({
        "success": True,
        "data": {
            "product": new_product.to_dict()
        }
    }), 201


@app.route("/api/v1/admin/product/<int:prod_id>/", methods=["PATCH"])
@expects_json(update_product_schema)
@required_roles("admin")
def edit_product(prod_id):
    fields = ["quantity", "product_name", "product_description",
              "category", "price", "img_url"]
    request_data = g.data

    if not request_data:
        abort(400, "No data provided")

    product_to_edit = Product.query.get(prod_id)
    if not product_to_edit:
        abort(404, "Product not found")
    sanitized_data = {k: v for k, v in request_data.items() if k in fields}

    if sanitized_data == {}:
        abort(400, "Please provide valid data")

    if sanitized_data.get("img_url") and not is_url(sanitized_data.get("img_url")):
        abort(400, "Invalid URL")

    for key, value in sanitized_data.items():
        setattr(product_to_edit, key, value)

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
    else:
        return jsonify({
            "success": True,
            "data": {
                "product": product_to_edit.to_dict()
            }
        })


@app.route("/api/v1/admin/product/<int:prod_id>/", methods=["DELETE"])
@required_roles("admin")
def delete(prod_id):
    product_to_delete = Product.query.get(prod_id)
    if not product_to_delete:
        return jsonify({
            "success": True,
            "message": "Product deleted",
            "product_id": prod_id
        })
    db.session.delete(product_to_delete)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:
        return jsonify({
            "success": True,
            "message": "Product deleted",
            "product_id": prod_id
        })


@app.route("/admin/inventory/report")
@required_roles("admin")
def generate_report():
    all_prods = Product.query.all()

    prod_list = []
    for i in all_prods:
        prod = i.to_dict()
        prod_list.append(prod)

    return jsonify({
        "success": True,
        "data": {
            "products": prod_list,
        }
    })


@app.route("/admin/sales/report")
@required_roles("admin")
def generate_sales():
    all_prods = Order.query.all()

    prod_list = []
    for i in all_prods:
        order_dets = OrderDetails.query.get(i.order_details_id)
        prod = {
            "customer_id": order_dets.customer_id,
            "product_id": i.product_id,
            "quantity": i.quantity,
            "order_date": order_dets.order_date,
            "to_street": order_dets.to_street,
            "to_city": order_dets.to_city,
            "zip": order_dets.zip
        }
        prod_list.append(prod)
    return jsonify({
        "success": True,
        "data": {
            "products": prod_list,
        }
    })


@app.route("/api/v1/admin/reviews/")
@required_roles("admin")
def get_reviews():
    page = request.args.get("page", 1, type=int)
    revs = Reviews.query.order_by(asc(Reviews.rating)).paginate(per_page=100, page=page)

    rev_list = [rev.to_dict() for rev in revs.items]

    return jsonify({
        "success": True,
        "data": {
            "reviews": rev_list
        },
        "pages": revs.pages,
        "current_page": revs.page,
        "per_page": 100,
    })


@app.route("/api/v1/admin/reviews/<int:rev_id>/", methods=["DELETE"])
@required_roles("admin")
def delete_review(rev_id):
    rev_to_delete = Reviews.query.get(rev_id)
    if not rev_to_delete:
        return jsonify({
            "success": True,
            "message": "Review deleted",
            "review_id": rev_id
        })
    db.session.delete(rev_to_delete)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:
        return jsonify({
            "success": True,
            "message": "Review deleted",
            "review_id": rev_id
        })


@app.route("/admin/customer")
@required_roles("admin")
def search_user():
    user = request.args.get("user")
    page = request.args.get("page", 1, int)
    try:
        result = Customer.query.filter(
            Customer.first_name.ilike(f"%{user}%") |
            Customer.last_name.ilike(f"%{user}%") |
            Customer.mail.ilike(f"%{user}%") |
            Customer.phone.ilike(f"%{user}%")).paginate(per_page=10, page=page)
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        rez_list = [customer.to_dict() for customer in result.items]

        return jsonify({"results": rez_list,
                        "success": True,
                        "pages": result.pages,
                        "current_page": result.page,
                        "per_page": 100,
                        })


@app.route("/api/v1/admin/user/<int:user_id>/role/", methods=["PATCH"])
@expects_json(update_role_schema)
@required_roles("admin")
def change_user_role(user_id):
    user = Customer.query.get(user_id)
    if not user:
        abort(404, "User not found")
    request_data = request.get_json()
    role = request_data.get("role", None)

    if not role:
        print("no role")
        abort(400, "Please provide a valid role")
    if role > 3 or role < 1:
        print("role not in range")
        abort(400)
    user.role = role
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:
        return jsonify({
            "success": True,
            "data": {
                "user_role": user.role,
                "user_id": user.id
            }

        })
