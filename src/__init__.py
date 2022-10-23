import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_session import Session
from flask_cors import CORS
from flask_bcrypt import Bcrypt


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_object("config")
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    CORS(app, resources={r"/*": {"origins": "*"}})

    return app


app = create_app()
app.permanent_session_lifetime = timedelta(days=30)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail_sender = Mail(app)
Session(app)
bcrypt = Bcrypt(app)


from . import (auth, products, admin_views,
               users, cart,
               payments, ratings,
               errorhandlers)
