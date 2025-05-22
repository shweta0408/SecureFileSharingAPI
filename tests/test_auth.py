import datetime
from werkzeug.security import generate_password_hash
import jwt
from app import mongo


def test_signup(client):
    response = client.post('/signup', json={
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    assert 'User created successfully' in response.json['message']


def test_signup_existing_user(client):
    # First signup
    client.post('/signup', json={
        'email': 'existinguser@example.com',
        'password': 'password123'
    })
    # Try to signup again with the same email
    response = client.post('/signup', json={
        'email': 'existinguser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 400
    assert 'User already exists' in response.json['message']


def test_login(client, app):
    # First, create a verified user
    with app.app_context():
        mongo.db.users.insert_one({
            'email': 'verifieduser@example.com',
            'password': generate_password_hash('password123'),
            'role': 'client',
            'verified': True
        })

    # Then try to log in
    response = client.post('/login', json={
        'email': 'verifieduser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'token' in response.json


def test_login_invalid_credentials(client):
    response = client.post('/login', json={
        'email': 'verifieduser@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert 'Invalid credentials' in response.json['message']


def test_login_unverified(client, app):
    # First, create an unverified user
    with app.app_context():
        mongo.db.users.insert_one({
            'email': 'unverifieduser@example.com',
            'password': generate_password_hash('password123'),
            'role': 'client',
            'verified': False
        })

    # Then try to log in
    response = client.post('/login', json={
        'email': 'unverifieduser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 401
    assert 'Please verify your email first' in response.json['message']


def test_verify_email(client, app):
    # Create an unverified user
    with app.app_context():
        user_id = mongo.db.users.insert_one({
            'email': 'toverify@example.com',
            'password': generate_password_hash('password123'),
            'role': 'client',
            'verified': False
        }).inserted_id

        # Generate a verification token
        token = jwt.encode({
            'user_id': str(user_id),
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'])

    # Verify the email
    response = client.get(f'/verify-email/{token}')
    assert response.status_code == 200
    assert 'Email verified successfully' in response.json['message']

    # Check that the user is now verified
    with app.app_context():
        user = mongo.db.users.find_one({'_id': user_id})
        assert user['verified']


def test_verify_email_invalid_token(client):
    response = client.get('/verify-email/invalid-token')
    assert response.status_code == 400
    assert 'Invalid verification link' in response.json['message']


def test_verify_email_expired_token(client, app):
    # Create an unverified user
    with app.app_context():
        user_id = mongo.db.users.insert_one({
            'email': 'toverify@example.com',
            'password': generate_password_hash('password123'),
            'role': 'client',
            'verified': False
        }).inserted_id

        # Generate an expired verification token
        token = jwt.encode({
            'user_id': str(user_id),
            'exp': datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'])

    # Verify the email
    response = client.get(f'/verify-email/{token}')
    assert response.status_code == 400
    assert 'Verification link has expired' in response.json['message']