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
    if app.config.get('TESTING'):
        from unittest.mock import MagicMock
        redis_client = MagicMock()
        redis_client.get.return_value = None
        redis_client.setex.return_value = True
        redis_client.delete.return_value = True
        redis_client.pipeline.return_value.__enter__ = MagicMock()
        redis_client.pipeline.return_value.execute = MagicMock()
        pipe = MagicMock()
        pipe.incr = MagicMock()
        pipe.expire = MagicMock()
        pipe.execute = MagicMock()
        redis_client.pipeline.return_value = pipe
    else:
        redis_client = redis.from_url(app.config['REDIS_URL'])

    app.config['SWAGGER'] = {
        'title': 'LinkForge URL Shortener API',
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
    from app.routes.auth import auth
    app.register_blueprint(url)
    app.register_blueprint(auth)

    with app.app_context():
        from app import models
        db.create_all()

    @app.route('/health')
    def health():
        return {"status": "ok"}

    return app