from flask import (url_for,
                   request,
                   jsonify, session, abort, g)
from flask_expects_json import expects_json

from src.helpers.errors import invalid_token_response
from src.helpers.auth_tokens import check_valid_header, decode_auth_token
from src.models import (Product,
                        Order, OrderDetails, Customer
                        )
from src import app, mail_sender, db
from flask_login import (login_required,
                         current_user)
from flask_mail import Message
from threading import Thread
from datetime import date
import stripe
import json
import os

from src.schema.defineSchema import checkout_schema

stripe.api_key = app.config['STRIPE_SECRET_KEY']
endpoint_secret = os.environ.get("endpoint_secret")


def send_mail(app, msg):
    with app.app_context():
        mail_sender.send(msg)


@app.route('/api/v1/user/<int:user_id>/payments/checkout/', methods=['POST'])
@expects_json(checkout_schema)
def create_checkout_session(user_id):
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    if not resp:
        return invalid_token_response()

    decoded_token = decode_auth_token(resp)

    if decoded_token != user_id:
        return invalid_token_response()
    request_data = g.data
    if "cart_dict" not in session:
        abort(404, "No items in cart")

    if session["cart_dict"] == {}:
        abort(404, "No items in cart")

    cart_dict = session["cart_dict"]

    items_to_buy = []
    for prod_id, quantity in cart_dict.items():
        product_to_buy = Product.query.get(prod_id)
        if not product_to_buy:
            abort(404, "Product not found")
        qty_left = product_to_buy.quantity
        if quantity > qty_left:
            abort(400, "Not enough items in stock")

        line_dict = {
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product_to_buy.product_description,
                },
                'unit_amount': int((product_to_buy.price / 744) * 100),
            },
            'quantity': quantity,

        }
        items_to_buy.append(line_dict)

    street = request_data.get("street", None)
    city = request_data.get("city", None)
    to_zip = request_data.get("zip", None)

    if not street or not city or not to_zip:
        abort(400)
    prod_ids = (str([*cart_dict.keys()]))
    prod_qty = (str([*cart_dict.values()]))

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=items_to_buy,
            mode='payment',
            success_url=url_for("success", user_id=user_id,
                                _external=True),
            cancel_url=url_for("cancel", _external=True),
            metadata={"prod_ids": prod_ids,
                      "prod_qty": prod_qty,
                      "street": street,
                      "city": city,
                      "zip": to_zip,
                      "user_id": user_id,
                      }

        )
    except Exception as e:
        app.logger.error(e)
        abort(500)
    else:
        return jsonify({
            "success": True,
            "stripe_url": checkout_session.url,
        }), 303


@app.route("/api/v1/payments/cancel/")
def cancel():
    return jsonify({
        "success": False,
        "message": "Transaction failed",
    })


@app.route("/api/v1/user/<int:user_id>/payments/success/", methods=["GET"])
def success(user_id):
    auth_header = request.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    if not resp:
        return invalid_token_response()
    decoded_token = decode_auth_token(resp)
    if decoded_token != user_id:
        return invalid_token_response()
    session["cart_dict"].clear()
    return jsonify({
        "success": True,
        "message": "Transaction successful"
    })


@app.route('/api/v1/payments/stripe-webhooks/', methods=['POST'])
def webhook():
    receipt_url = ""
    payload = request.data
    event = None

    try:
        event = json.loads(payload)
    except Exception as e:
        app.logger.error('??  Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False)
    if endpoint_secret:
        # Only verify the event if there is an endpoint secret defined
        # Otherwise use the basic event deserialized with json
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            app.logger.error('Webhook signature verification failed.' + str(e))
            return jsonify(success=False)

        # Handle the event
    if event and event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        app.logger.info('Payment for {} succeeded'.format(payment_intent['amount']))
        receipt_url = (payment_intent["charges"]["data"][0]["receipt_url"])
        print("payment intent succeeded")


    elif event['type'] == 'payment_intent.payment_failed':
        return jsonify({
            "success": False,
            "error": "payment_intent failed",
        }), 400
    else:
        # Unexpected event type
        app.logger.info('Unhandled event type {}'.format(event['type']))
    if event['type'] == 'checkout.session.completed':
        app.logger.info('Checkout session completed')

        session_completed = event['data']["object"]
        user = Customer.query.get(int(session_completed['metadata']['user_id']))
        customer_order = OrderDetails(
            customer_name=user,
            to_street=session_completed['metadata']['street'],
            to_city=session_completed['metadata']['city'],
            zip=session_completed['metadata']['zip'],
            order_date=date.today()
        )
        product_ids = (
            session_completed["metadata"]["prod_ids"]).replace("[",
                                                               "").replace("]",
                                                                           "").split(",")
        product_qty = (
            session_completed["metadata"]["prod_qty"]).replace("[",
                                                               "").replace("]",
                                                                           "").split(",")
        db.session.add(customer_order)
        for index, item in enumerate(product_ids):
            app.logger.info("adding order")
            prod = Product.query.get(int(item))
            prod.quantity -= int(product_qty[index])
            order = Order(
                product_name=prod,
                quantity=int(item),
                order_name=customer_order
            )
            db.session.add(order)
        try:
            db.session.commit()
        except Exception as e:
            app.logger.error(e)
            abort(500)

        msg = Message()
        msg.subject = "Receipt from laptohaven"
        msg.recipients = [user.mail]
        msg.body = f'Thanks for your patronage, do come again, Here is the link to your receipt{receipt_url}'
        # msg.html = template
        Thread(target=send_mail, args=(app, msg)).start()

    print("successfully sent mail and added to db")
    return jsonify(success=True)
