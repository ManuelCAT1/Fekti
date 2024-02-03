from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

import logging

logging.basicConfig(filename='email.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


db = SQLAlchemy()
DB_NAME = "database.db"
mail = Mail()  # Initialize mail
s = URLSafeTimedSerializer('SuperFektiXDUnpredictableKey')
def create_app(environ=None, start_response=None):
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'


    def custom_b64encode(value):
        if isinstance(value, bytes):  # Check if value is bytes
            encoded_data = base64.b64encode(value).decode('utf-8')
        else:
            encoded_data = base64.b64encode(value.encode('utf-8')).decode('utf-8')
        return encoded_data

    # Register the filter globally
    app.jinja_env.filters['custom_b64encode'] = custom_b64encode


    app.config['SECRET_KEY'] = 'SuperFektiXDUnpredictableKey'
    app.config['SECURITY_PASSWORD_SALT'] = 'AnotherSuperFektiXDUnpredictableKey'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    # Email configuration
    app.config['MAIL_SERVER'] = 'serwer2395047.home.pl'
 
    app.config['MAIL_PORT'] = 587
  
    app.config['MAIL_USE_TLS'] = True  # Enable TLS
    
    app.config['MAIL_USE_SSL'] = False  # Keep SSL disabled
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'weryfikacja@fekti.com')

    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '8@_cLZ4rvFLF9b5')
 
    app.config['MAIL_DEFAULT_SENDER'] = 'weryfikacja@fekti.com'
 
    db.init_app(app)

    mail.init_app(app)  # Initialize mail with the app



    

    with app.app_context():
        db.create_all()



    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Photo



    login_manager = LoginManager()
    login_manager.login_view = 'auth.loginPage'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    from . import models

    with app.app_context():
        db.create_all()




    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



    app.logger.info('GateEND')
    return app


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}




