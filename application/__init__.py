#JPUSH Required to install dependencies
import jpush
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.debug = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
#JPUSH INITIAL CODES
_jpush = jpush.JPush('fdb88b0505356aa4e0f00c07', '2366dd3a2925aaea5a21999a')
_jpush.set_logging("DEBUG")
from . import routes, models

