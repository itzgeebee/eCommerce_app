from flask import (url_for,
                   request,
                   jsonify, session, abort)
from online_store.models import (Product,
                                 Order, OrderDetails,Customer
                                 )
from online_store import app, mail_sender, db
from flask_login import (login_required,
                         current_user)
from flask_mail import Message
from threading import Thread
from datetime import date
import stripe
import json
import os

stripe.api_key = app.config['STRIPE_SECRET_KEY']
endpoint_secret = os.environ.get("endpoint_secret")


def send_mail(app, msg):
    with app.app_context():
        mail_sender.send(msg)


@app.route('/payments/checkout', methods=['POST'])
@login_required
def create_checkout_session():
    request_data = request.get_json()
    if "cart_dict" not in session:
        abort(404)

    if session["cart_dict"] == {}:
        abort(404)

    cart_dict = session["cart_dict"]

    items_to_buy = []
    for item in cart_dict:
        product_to_buy = Product.query.get(int(item))
        qty = int(cart_dict[item])
        qty_left = product_to_buy.quantity
        if qty > qty_left:
            abort(400)

        line_dict = {
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product_to_buy.product_description,
                },
                'unit_amount': (product_to_buy.price // 600) * 100,
            },
            'quantity': qty,

        }
        items_to_buy.append(line_dict)

    strt = request_data.get("street", None)
    cty = request_data.get("city", None)
    to_zip = request_data.get("zip", None)

    if not strt or not cty or not to_zip:
        abort(400)
    prod_ids = (str([*cart_dict.keys()]))
    prod_qty = (str([*cart_dict.values()]))

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=items_to_buy,
            mode='payment',
            success_url=url_for("success",
                                _external=True),
            cancel_url=url_for("cancel", _external=True),
            metadata={"prod_ids": prod_ids,
                      "prod_qty": prod_qty,
                      "street": strt,
                      "city": cty,
                      "zip": to_zip,
                      "user_id": current_user.id
                      }

        )
    except Exception as e:
        return str(e)

    # return redirect(checkout_session.url, code=303)
    return jsonify({
        "success": True,
        "logged_in": current_user.is_authenticated,
        "stripe_url": checkout_session.url,
    }), 303


@app.route("/payments/cancel")
def cancel():
    return jsonify({
        "success": False,
        "message": "Transaction failed",
        "logged_in": current_user.is_authenticated
    })


@app.route("/payments/success", methods=["GET"])
@login_required
def success():
    session["cart_dict"].clear()
    return jsonify({
        "success": True,
        "logged_in": current_user.is_authenticated,
    })


@app.route('/payments/stripe-webhook', methods=['POST'])
def webhook():
    event = None
    receipt_url = ""
    payload = request.data

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


    elif event['type'] == 'payment_intent.payment_failed':
        return jsonify({
            "success": False,
            "error": "payment_intent failed",
        }), 400
    else:
        # Unexpected event type
        app.logger.info('Unhandled event type {}'.format(event['type']))
    if event['type'] == 'checkout.session.completed':

        session_completed = event['data']["object"]
        user = Customer.query.get(int(session_completed['metadata']['user_id']))
        customer_order = OrderDetails(
            customer_name=user,
            to_street=session_completed['metadata']['street'],
            to_city=session_completed['metadata']['city'],
            zip=session_completed['metadata']['zip'],
            order_date=date.today()
        )
        product_ids = (session_completed["metadata"]["prod_ids"]).replace("[", "").replace("]", "").split(",")
        product_qty = (session_completed["metadata"]["prod_qty"]).replace("[", "").replace("]", "").split(",")
        db.session.add(customer_order)
        for index, item in enumerate(product_ids):
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

    return jsonify(success=True)
