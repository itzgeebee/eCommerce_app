import os
from flask import (render_template, redirect,
                   url_for, request,
                   send_file, session, jsonify)
from sqlalchemy import asc

from online_store.models import (Customer, Product, Order,
                                 Reviews, OrderDetails, Role)
from werkzeug.exceptions import abort
from online_store import app, login_manager
from flask_login import current_user
from online_store import db
from functools import wraps
from online_store.forms import UploadForm
import csv


@login_manager.user_loader
def load_user(id):
    return Customer.query.get(id)


def required_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(403, description="Forbidden! You do not have access to this page")
            role_id = current_user.role
            get_role = Role.query.get(role_id)
            get_role = get_role.to_dict()
            if get_role["name"] not in roles:
                return abort(403, description="Forbidden! You do not have access to this page")
            return f(*args, **kwargs)

        return decorated_function

    return wrapper


@app.route("/admin", methods=["GET", "POST"])
@required_roles("Admin")
def admin_home():
    return jsonify({
        "success": True,
        "logged_in": current_user.is_authenticated
    })


@app.route("/admin/inventory", methods=["GET"])
@required_roles("Admin")
def inventory():
    try:
        os.remove(os.path.abspath(os.getcwd()) + "/Inventory.csv")
    except FileNotFoundError:
        pass
    page = request.args.get("page", 1, type=int)

    all_prods = Product.query.order_by(Product.quantity.asc()).paginate(per_page=100, page=page)
    if not all_prods:
        abort(404)

    prod_list = [product.to_dict() for product in all_prods.items]

    return jsonify({
        "success": True,
        "logged_in": current_user.is_authenticated,
        "products": prod_list,
        "pages": all_prods.pages,
        "current_page": all_prods.page,
        "per_page": 100,
    })


@app.route("/admin/product/<int:prod_id>", methods=["PATCH"])
@required_roles("Admin")
def restock(prod_id):
    product = Product.query.get(prod_id)
    if not product:
        abort(404)
    product.quantity = 100
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:

        return jsonify({
            "success": True,
            "logged": current_user.is_authenticated,
            "product_id": prod_id
        })


@app.route("/admin/sales")
@required_roles("Admin")
def sales():
    try:
        os.remove(os.path.abspath(os.getcwd()) + "/Sales.csv")
    except FileNotFoundError:
        pass
    page = request.args.get("page", 1, type=int)
    all_sales = Order.query.order_by(Order.quantity.desc()).paginate(per_page=100, page=page)
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
        "logged_in": current_user.is_authenticated,
        "sales": sales_list,
        "pages": all_sales.pages,
        "current_page": all_sales.page,
        "per_page": 100,
    })


@app.route("/admin/product", methods=["POST"])
@required_roles("Admin")
def upload():
    request_data = request.get_json()
    quantity = request_data.get("quantity", None)
    product_name = request_data.get("product_name", None)
    product_description = request_data.get("description", None)
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
        "logged_in": current_user.is_authenticated,
        "product": new_product.to_dict()
    })


@app.route("/admin/product/<int:prod_id>", methods=["PUT"])
@required_roles("Admin")
def edit_product(prod_id):
    request_data = request.get_json()

    product_to_edit = Product.query.get(prod_id)
    print(product_to_edit)
    if not product_to_edit:
        abort(404)
    quantity = request_data.get("quantity", None)
    product_name = request_data.get("product_name", None)
    product_description = request_data.get("description", None)
    category = request_data.get("category", None)
    price = request_data.get("price", None)
    img_url = request_data.get("img_url", None)

    product_to_edit.quantity = quantity
    product_to_edit.product_name = product_name
    product_to_edit.product_description = product_description
    product_to_edit.category = category
    product_to_edit.price = price
    product_to_edit.img_url = img_url
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
    else:
        return jsonify({
            "success": True,
            "logged_in": current_user.is_authenticated,
            "product_id": prod_id
        })


@app.route("/admin/product/<int:prod_id>", methods=["DELETE"])
@required_roles("Admin")
def delete(prod_id):
    product_to_delete = Product.query.get(prod_id)
    if not product_to_delete:
        abort(404)
    db.session.delete(product_to_delete)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:
        return jsonify({
            "success": True,
            "logged_in": current_user.is_authenticated,
            "product_id": prod_id
        })


@app.route("/admin/inventory/report")
@required_roles("Admin")
def generate_report():
    all_prods = Product.query.all()

    prod_list = []
    for i in all_prods:
        prod = i.to_dict()
        prod_list.append(prod)
    csv_columns = ["id", "quantity", "product_name", "product_description", "category", "price", "img_url"]
    csv_file = os.path.abspath(os.getcwd()) + "/Inventory.csv"

    try:
        with open(csv_file, 'w', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in prod_list:
                writer.writerow(data)
    except IOError as e:
        app.logger.error(e)

    return send_file(csv_file, as_attachment=True)


@app.route("/admin/sales/report")
@required_roles("Admin")
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
    csv_columns = ["id", "customer_id", "product_id", "quantity", "to_street", "to_city", "zip", "order_date"]
    csv_file = os.path.abspath(os.getcwd()) + "\Sales.csv"

    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in prod_list:
                writer.writerow(data)
    except IOError as e:
        app.logger.error(e)

    return send_file(csv_file, as_attachment=True)


@app.route("/admin/reviews")
@required_roles("Admin")
def get_reviews():
    page = request.args.get("page", 1, type=int)
    revs = Reviews.query.order_by(asc(Reviews.rating)).paginate(per_page=100, page=page)
    if not revs:
        abort(404)
    rev_list = [rev.to_dict() for rev in revs.items]

    return jsonify({
        "success": True,
        "logged_in": current_user.is_authenticated,
        "reviews": rev_list,
        "pages": revs.pages,
        "current_page": revs.page,
        "per_page": 100,
    })


@app.route("/admin/reviews/<int:rev_id>", methods=["DELETE"])
@required_roles("Admin")
def delete_review(rev_id):
    rev_to_delete = Reviews.query.get(rev_id)
    if not rev_to_delete:
        abort(404)
    db.session.delete(rev_to_delete)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        abort(422)
    else:
        return jsonify({
            "success": True,
            "logged_in": current_user.is_authenticated,
            "review_id": rev_id,
        })


@app.route("/admin/customer")
@required_roles("Admin")
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
                        "logged_in": current_user.is_authenticated,
                        "pages": result.pages,
                        "current_page": result.page,
                        "per_page": 100,
                        })


@app.route("/admin/user/<int:user_id>/role", methods=["PATCH"])
@required_roles("Admin")
def change_user_role(user_id):
    user = Customer.query.get(user_id)
    if not user:
        abort(404)
    request_data = request.get_json()
    role = request_data.get("role", None)

    if not role:
        print("no role")
        abort(400)
    role = int(role)
    if type(role) is not int:
        print("not int", type(role))
        abort(400)
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
            "logged_in": current_user.is_authenticated,
            "user_role": user.role,
            "user_id": user.id
        })


