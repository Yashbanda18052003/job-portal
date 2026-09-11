import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_change_in_production")
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///jobportal.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
