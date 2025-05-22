from flask import current_app
from app import mongo
from app.models import User
import jwt
import datetime
from bson.objectid import ObjectId
from smtp2go.core import Smtp2goClient


payload = """
Hello,
This email address was used to create an account in Secure File-Sharing System:

------------------------------------------
email: %s
time: %s UTC
------------------------------------------

Click the link below to verify your email address. This link will expire in 24 hours.
%s

If this isn't you, please ignore this email.
"""


def signup_user(email, password):
    existing_user = mongo.db.users.find_one({'email': email})
    if existing_user:
        return {'message': 'User already exists!'}, 400

    new_user = User(email, password)
    result = new_user.save()

    verification_token = jwt.encode({
        'user_id': str(result.inserted_id),
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'])

    if not current_app.config['TESTING']:
        verification_url = current_app.config['BASE_URL'] + f"/verify-email/{verification_token}"
        smtp_client = Smtp2goClient(current_app.config['SMTP2GO_API_KEY'])
        smtp_client.send(sender=current_app.config['SMTP2GO_SENDER'],
                         recipients=[email],
                         subject='Email Verification - Secure File Sharing System',
                         text=payload % (email, str(datetime.datetime.now(datetime.UTC))[:19], verification_url))

    return {'message': 'User created successfully. '
                       'Check your email for verification link. '
                       'It will expire in 24 hours.'}, 201


def verify_email(token):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user = mongo.db.users.find_one({'_id': ObjectId(data['user_id'])})
        if user:
            mongo.db.users.update_one({'_id': ObjectId(data['user_id'])}, {'$set': {'verified': True}})
            return {'message': 'Email verified successfully'}, 200
        else:
            return {'message': 'User not found'}, 404
    except jwt.ExpiredSignatureError:
        return {'message': 'Verification link has expired'}, 400
    except jwt.InvalidTokenError:
        return {'message': 'Invalid verification link'}, 400


def login_user(email, password):
    user = mongo.db.users.find_one({'email': email})
    if user and User.check_password(user['password'], password):
        if user['role'] == 'client' and not user['verified']:
            return {'message': 'Please verify your email first'}, 401
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
        }, current_app.config['SECRET_KEY'])
        return {'token': token}, 200
    return {'message': 'Invalid credentials'}, 401
