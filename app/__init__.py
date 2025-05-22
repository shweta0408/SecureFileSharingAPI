from flask import Flask
from flask_pymongo import PyMongo
from app.config import Config

mongo = PyMongo()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    mongo.init_app(app)
    mongo.db = mongo.cx['sfss']

    from app.routes import auth, files
    app.register_blueprint(auth.bp)
    app.register_blueprint(files.bp)

    return app
