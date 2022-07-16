from flask import (request, jsonify, abort, render_template)
from sqlalchemy import desc, func
from online_store.models import (Customer, Product,
                                 Reviews, Order)
from online_store import app, db, login_manager
from flask_login import current_user, login_required


@login_manager.user_loader
def load_user(id):
    return Customer.query.get(id)
@app.route("/")
def get_index_page():
    return render_template('index.html')

@app.route("/api", methods=["GET"])
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
                    "laptop": laptop_category,
                    "most_purchased": most_purchased_prods,
                    "highly_rated": highly_rated_prods}

    except Exception as e:
        app.logger.error(e)
        abort(404)
    else:
        product_format = jsonify({
            'products': products,
            'success': True,
            'logged_in': current_user.is_authenticated
        })
        return product_format


@app.route("/product")
def product():
    product_id = request.args.get("id", None)
    specific_product = Product.query.get(product_id)
    if not specific_product:
        abort(404)

    all_reviews = Reviews.query.filter_by(product_id=product_id)
    average_rating = Reviews.query.with_entities(func.avg(Reviews.rating).label("average"
                                                                                )).filter_by(
        product_id=product_id).all()

    all_reviews = [review.to_dict() for review in all_reviews]
    average_rating = round(int(average_rating[0][0]), 1)

    if specific_product:
        prod_orders = [i.order_name.to_dict() for i in specific_product.order]
        specific_product = specific_product.to_dict()
        product_format = jsonify({
            'prod_orders': prod_orders,
            'product': specific_product,
            'logged_in': current_user.is_authenticated,
            'average_rating': average_rating,
            'all_reviews': all_reviews,
            'success': True,
        })

        return product_format

    else:
        app.logger.error('Product not found error')
        abort(404)


@app.route("/category/<category>")
def phones(category):
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
        abort(404)
    else:
        result_list = [{"id": result.id,
                        "img_url": result.img_url,
                        "product_description": result.product_description,
                        "price": result.price
                        } for result in query_result.items]

        category = category
        result_format = jsonify({
            "result": result_list,
            "success": True,
            "logged_in": current_user.is_authenticated,
            "category": category,
            "pages": query_result.pages,
            "current_page": query_result.page,
            "per_page": 20,
        })
        return result_format


@app.route("/rated")
def rated():
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

        result_format = jsonify({
            "result": result_list,
            "success": True,
            "logged_in": current_user.is_authenticated,
            "category": "highly rated",
            "pages": query_result.pages,
            "current_page": query_result.page,
            "per_page": 20,
        })
        return result_format


@app.route("/purchased")
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

        result_format = jsonify({
            "result": result_list,
            "success": True,
            "logged_in": current_user.is_authenticated,
            "category": "most purchased",
            "pages": query_result.pages,
            "current_page": query_result.page,
            "per_page": 20,
        })
        return result_format


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get('query', None)

    if query:
        page = request.args.get("page", 1, type=int)
        try:
            query_result = Product.query.with_entities(Product.id,
                                                       Product.img_url,
                                                       Product.price,
                                                       Product.product_description
                                                       ).filter(
                Product.product_name.ilike(f"%{query}%") | Product.product_description.ilike(f"%{query}%")
                | Product.category.ilike(f"%{query}%")).paginate(per_page=20, page=page)
        except Exception as e:
            app.logger.error(e)
            abort(404)
        else:
            if query_result:
                result_list = [{"id": result.id,
                                "img_url": result.img_url,
                                "product_description": result.product_description,
                                "price": result.price
                                } for result in query_result.items]

                result_format = jsonify({
                    "result": result_list,
                    "success": True,
                    "logged_in": current_user.is_authenticated,
                    "pages": query_result.pages,
                    "current_page": query_result.page,
                    "per_page": 20,
                })
                return result_format
            else:
                abort(404)
    else:
        app.logger.error("No query error")
        abort(404)


@app.route("/filter", methods=["GET"])
def filter_product():
    max_price = request.args.get("max", None)
    min_price = request.args.get("min", None)
    category = request.args.get("category", None)
    if max_price and min_price and category and (max_price > min_price):
        page = request.args.get("page", 1, type=int)
        try:
            query_result = Product.query.with_entities(Product.id,
                                                       Product.img_url,
                                                       Product.price,
                                                       Product.product_description
                                                       ).filter(
                Product.price > min_price,
                Product.price < max_price,
                Product.category == category).paginate(per_page=20, page=page)
        except Exception as e:
            app.logger.error(e)
            abort(404)
        else:
            if query_result:
                result_list = [{"id": result.id,
                                "img_url": result.img_url,
                                "product_description": result.product_description,
                                "price": result.price
                                } for result in query_result.items]

                result_format = jsonify({
                    "result": result_list,
                    "success": True,
                    "logged_in": current_user.is_authenticated,
                    "pages": query_result.pages,
                    "current_page": query_result.page,
                    "per_page": 20,
                })
                return result_format
            else:
                app.logger.error("No result found")
                abort(404)
    else:
        app.logger.error("Invalid argument error")
        abort(404)


@app.route("/product/<prodId>/rating", methods=["POST"])
@login_required
def add_rating(prodId):
    prod = Product.query.get(prodId)
    data = request.get_json()
    rating = data.get("rating", None)
    review = data.get("review", None)

    if not rating or not review:
        abort(400)
    if rating < 1 or rating > 5:
        abort(400)
    new_review = Reviews(
        review=review,
        rating=rating,
        customer=current_user,
        product=prod
    )
    db.session.add(new_review)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        db.session.rollback()
        abort(422)
    finally:
        db.session.close()

    return jsonify({"success": True,
                    "logged_in": current_user.is_authenticated})
