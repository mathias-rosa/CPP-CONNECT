import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail

import pymongo

# Configuration génerale de l'application

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'VERY_SECRET_KEY'
host = os.environ.get('MONGODB_URI', 'mongodb+srv://schlogel:vendredi13@cluster0.aec0qny.mongodb.net/test')
client = pymongo.MongoClient(host=host)
mongodb = client.cpp_connect
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# configuration de flask_mail
app.config['MAIL_SERVER']='in-v3.mailjet.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


mail = Mail(app)

from app import routes
from app import api
from app import notes
