from app.utils.decorators import token_required
from flask import jsonify


def test_token_required_valid_token(app, client, auth_headers):
    @app.route('/test-auth')
    @token_required
    def test_auth(current_user):
        return jsonify({'message': 'Authenticated', 'user_email': current_user['email']})

    response = client.get('/test-auth', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == 'Authenticated'
    assert response.json['user_email'] == 'test@example.com'


def test_token_required_missing_token(app, client):
    @app.route('/test-auth')
    @token_required
    def test_auth(current_user):
        return jsonify({'message': 'Authenticated'})

    response = client.get('/test-auth')
    assert response.status_code == 401
    assert response.json['message'] == 'Token is missing!'


def test_token_required_invalid_token(app, client):
    @app.route('/test-auth')
    @token_required
    def test_auth(current_user):
        return jsonify({'message': 'Authenticated'})

    headers = {'Authorization': 'invalid_token'}
    response = client.get('/test-auth', headers=headers)
    assert response.status_code == 401
    assert response.json['message'] == 'Token is invalid!'
