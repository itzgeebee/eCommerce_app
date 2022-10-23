from flask import (request, jsonify, abort, render_template, Blueprint)
from sqlalchemy import desc, func

from src.helpers.errors import invalid_token_response
from src.helpers.auth_tokens import check_valid_header, decode_auth_token
from src.models import (Customer, Product,
                        Reviews, Order)
from src import app, db


@app.route("/")
def get_index_page():
    return render_template('index.html')


def transform_response(
        result_list, query_result, category=""):
    """
    :param result_list: The list containing query result
    :type result_list: list
    :param category: The category of the query
    :type category: str
    :param query_result: result of the query
    :type query_result: dict
    :return: json format of the query
    :rtype: object
    """

    return jsonify({

        "success": True,
        "data": {
            "products": result_list,
            "category": category,
            "pages": query_result.pages,
            "current_page": query_result.page,
            "per_page": 20
        }
    })


@app.route("/api/v1/", methods=["GET"])
def home():
    try:
        phone_cat = Product.query.filter_by(category="Phone").limit(4).all()
        laptop_cat = Product.query.filter_by(category="Laptop").limit(4).all()
        highly_rated = Product.query.select_from(
            Product).join(Reviews).group_by(Product.id).order_by(desc(func.avg(Reviews.rating))
                                                                 ).limit(4).all()
        most_purchased = Product.query.select_from(
            Product).join(Order).group_by(Product.id).order_by(desc(func.sum(Order.quantity))
                                                               ).limit(4).all()
        phone_category = [phone.to_dict() for phone in phone_cat]
        laptop_category = [laptop.to_dict() for laptop in laptop_cat]
        highly_rated_prods = [prod.to_dict() for prod in highly_rated]
        most_purchased_prods = [prod.to_dict() for prod in most_purchased]
        products = {"phones": phone_category,
                    "laptops": laptop_category,
                    "most_purchased": most_purchased_prods,
                    "highly_rated": highly_rated_prods}

    except Exception as e:
        app.logger.error(e)
        abort(404)
    else:
        product_format = jsonify({
            "data": {
                'products': products
            },
            'success': True,
        })
        return product_format


@app.route("/api/v1/product/<int:productId>/")
def product(productId):
    specific_product = Product.query.get(productId)
    if not specific_product:
        abort(404, "Product not found")
    all_reviews = Reviews.query.filter_by(product_id=productId)
    average_rating = Reviews.query.with_entities(func.avg(Reviews.rating).label("average"
                                                                                )).filter_by(
        product_id=productId).all()

    all_reviews = [review.to_dict() for review in all_reviews]
    if average_rating[0][0]:
        average_rating = round(average_rating[0][0], 1)
    average_rating = None

    prod_orders = [i.order_name.to_dict() for i in specific_product.order]
    specific_product = specific_product.to_dict()
    product_format = jsonify({
        "data": {

            'prod_orders': prod_orders,
            'product': specific_product,
            'average_rating': average_rating,
            'all_reviews': all_reviews
        },
        'success': True,
    })

    return product_format


@app.route("/api/v1/product/category/<category>/")
def get_by_category(category):
    try:
        page = request.args.get("page", 1, type=int)
        query_result = Product.query.with_entities(Product.id,
                                                   Product.img_url,
                                                   Product.price,
                                                   Product.product_description
                                                   ).filter_by(
            category=category).paginate(
            per_page=20, page=page
        )
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        result_list = [{"id": result.id,
                        "img_url": result.img_url,
                        "product_description": result.product_description,
                        "price": result.price
                        } for result in query_result.items]

        return transform_response(result_list, query_result, category=category)


@app.route("/api/v1/products/rating/")
def get_by_rating():
    try:
        page = request.args.get("page", 1, type=int)
        query_result = db.session.query(Product).select_from(
            Product).join(Reviews).group_by(Product.id).order_by(desc(func.avg(Reviews.rating))
                                                                 ).paginate(
            per_page=20, page=page
        )
    except Exception as e:
        app.logger.error(e)
        abort(404)
    else:
        result_list = [{"id": result.id,
                        "img_url": result.img_url,
                        "product_description": result.product_description,
                        "price": result.price
                        } for result in query_result.items]

        category = "highly_rated"

        return transform_response(result_list, query_result, category=category)


@app.route("/api/v1/products/most-purchased/")
def purchased():
    try:
        page = request.args.get("page", 1, type=int)
        query_result = db.session.query(Product).select_from(
            Product).join(Order).group_by(Product.id).order_by(desc(func.sum(Order.quantity))
                                                               ).paginate(
            per_page=20, page=page
        )
    except Exception as e:
        app.logger.error(e)
        abort(404)
    else:

        result_list = [{"id": result.id,
                        "img_url": result.img_url,
                        "product_description": result.product_description,
                        "price": result.price
                        } for result in query_result.items]

        category = "most_purchased"

        return transform_response(result_list, query_result, category=category)


@app.route("/api/v1/products/search/", methods=["GET"])
def search():
    query = request.args.get('query', None)
    if not query:
        app.logger.error("No query error")
        abort(404, "No query provided")

    page = request.args.get("page", 1, type=int)
    try:
        query_result = Product.query.with_entities(Product.id,
                                                   Product.img_url,
                                                   Product.price,
                                                   Product.product_description
                                                   ).filter(
            Product.product_name.ilike(f"%{query}%") | Product.product_description.ilike(
                f"%{query}%")
            | Product.category.ilike(f"%{query}%")).paginate(per_page=20, page=page)
    except Exception as e:
        app.logger.error(e)
        abort(404)
    else:
        result_list = [{"id": result.id,
                        "img_url": result.img_url,
                        "product_description": result.product_description,
                        "price": result.price
                        } for result in query_result.items]

        return transform_response(result_list, query_result)


@app.route("/api/v1/products/filter/", methods=["GET"])
def filter_product():
    max_price = int(request.args.get("max", None))
    min_price = int(request.args.get("min", None))
    category = request.args.get("category", None)
    if max_price and min_price and category and (max_price > min_price):
        page = request.args.get("page", 1, type=int)
        try:
            query_result = Product.query.with_entities(Product.id,
                                                       Product.img_url,
                                                       Product.price,
                                                       Product.product_description
                                                       ).filter(
                Product.price >= min_price,
                Product.price <= max_price,
                Product.category == category).paginate(per_page=20, page=page)
        except Exception as e:
            app.logger.error(e)
            abort(404)
        else:
            result_list = [{"id": result.id,
                            "img_url": result.img_url,
                            "product_description": result.product_description,
                            "price": result.price
                            } for result in query_result.items]

            return transform_response(result_list, query_result)

    else:
        app.logger.error("Invalid argument error")
        abort(404, "Invalid arguments provided")


