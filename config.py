import os
import logging
from dotenv import load_dotenv


load_dotenv()
file_path = os.path.abspath(os.getcwd()) + "/test.db"
logging.basicConfig(filename="error.log", level=logging.DEBUG,
                    format=f"%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s")
SECRET_KEY = os.environ.get("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URL", file_path)
SQLALCHEMY_TRACK_MODIFICATIONS = False
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get("EMAIL")
MAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("EMAIL")
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_PRIVATE")
SESSION_TYPE = "filesystem"
DEBUG = True
CORS_METHODS = ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"]
# SERVER_NAME = "gadgehaven.herokuapp.com"


