import pytest
from app import create_app
from app import mongo
from werkzeug.security import generate_password_hash
import jwt
import datetime


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'tests/uploads'
    mongo.db = mongo.cx['sfss_test']

    with app.app_context():
        mongo.db.users.delete_many({})
        mongo.db.files.delete_many({})

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    user = {
        'email': 'test@example.com',
        'password': generate_password_hash('password'),
        'role': 'client',
        'verified': True
    }
    with app.app_context():
        user_id = mongo.db.users.insert_one(user).inserted_id
        token = jwt.encode({
            'user_id': str(user_id),
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'])

    return {'Authorization': token}


@pytest.fixture
def ops_headers(app):
    user = {
        'email': 'ops@example.com',
        'password': generate_password_hash('password'),
        'role': 'ops',
        'verified': True
    }
    with app.app_context():
        user_id = mongo.db.users.insert_one(user).inserted_id
        token = jwt.encode({
            'user_id': str(user_id),
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'])

    return {'Authorization': token}
