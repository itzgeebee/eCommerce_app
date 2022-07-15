import os
from datetime import timedelta
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_gravatar import Gravatar
from flask_mail import Mail
from flask_migrate import Migrate
from flask_session import Session
from flask_cors import CORS


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

    return app


app = create_app()
CORS(app, resources={r"/*": {"origins": "*"}})
login_manager = LoginManager()
login_manager.init_app(app)
app.permanent_session_lifetime = timedelta(days=30)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail_sender = Mail(app)
Bootstrap(app)
Session(app)

gravatar = Gravatar(app,
                    size=50,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

from online_store import (queries, admin_views,
                          users, cart,
                          payments, errorhandlers)
