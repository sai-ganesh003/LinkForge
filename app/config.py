import os
from dotenv import load_dotenv

load_dotenv(override=False)

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-secret')
    JWT_ACCESS_TOKEN_EXPIRES = 900
    JWT_REFRESH_TOKEN_EXPIRES = 604800
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')