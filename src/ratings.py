from flask import request, jsonify, abort, g
from flask_expects_json import expects_json

from src import app, db
from src.helpers.auth_tokens import check_valid_header, decode_auth_token
from src.helpers.errors import invalid_token_response
from src.models import Customer, Reviews, Product
from src.schema.defineSchema import add_rating_schema


@app.route("/api/v1/product/<int:prodId>/reviews/", methods=["POST"])
@expects_json(add_rating_schema)
def add_rating(prodId):
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    decoded_token = decode_auth_token(resp)
    if not resp:
        return invalid_token_response()

    customer_id = decoded_token
    data = g.data
    rating = data.get("rating", None)
    review = data.get("review", None)
    new_review = Reviews(
        review=review,
        rating=rating,
        product_id=prodId,
        customer_id=customer_id)
    db.session.add(new_review)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(e)
        db.session.rollback()
        abort(422, e.args[0])
    finally:
        db.session.close()

    return jsonify({"success": True,
                    "message": "Review added successfully"}), 201
