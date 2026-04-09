import os
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from app.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
redis_client = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    global redis_client
    redis_client = redis.from_url(app.config['REDIS_URL'])

    app.config['SWAGGER'] = {
        'title': 'URL Shortener API',
        'uiversion': 3,
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'Enter: Bearer <your_token>'
            }
        }
    }
    Swagger(app)

    from app.routes.url import url
    app.register_blueprint(url)

    with app.app_context():
        from app import models
        db.create_all()

    @app.route('/health')
    def health():
        return {"status": "ok"}

    return app