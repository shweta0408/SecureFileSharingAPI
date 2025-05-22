import datetime
import jwt
from app import mongo
import io


def test_upload_file(client, ops_headers):
    with open('tests/test.docx', 'rb') as file:
        data = {
            'file': (io.BytesIO(file.read()), 'test.docx')
        }
        response = client.post('/upload', data=data, headers=ops_headers)
        assert response.status_code == 201
        assert 'file_id' in response.json


def test_upload_file_not_ops(client, auth_headers):
    data = {
        'file': (io.BytesIO(b"test file content"), 'test.docx')
    }
    response = client.post('/upload', data=data, headers=auth_headers)
    assert response.status_code == 403
    assert response.json['message'] == 'You are not allowed to upload files'


def test_upload_file_no_file(client, ops_headers):
    data = {
        'file': (io.BytesIO(b""), '')
    }
    response = client.post('/upload', data=data, headers=ops_headers)
    assert response.status_code == 400
    print(response)
    assert response.json['message'] == 'No file selected for uploading'


def test_upload_file_invalid_file_type(client, ops_headers):
    data = {
        'file': (io.BytesIO(b"test file content"), 'test.txt')
    }
    response = client.post('/upload', data=data, headers=ops_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Allowed file types are pptx, docx, xlsx'


def test_list_files(client, auth_headers, app):
    # First, add some files to the database
    with app.app_context():
        mongo.db.files.insert_many([
            {'file_id': '1', 'filename': 'file1.docx'},
            {'file_id': '2', 'filename': 'file2.xlsx'},
        ])

    response = client.get('/files', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) == 2
    assert {'file_id': '1', 'filename': 'file1.docx'} in response.json
    assert {'file_id': '2', 'filename': 'file2.xlsx'} in response.json


def test_generate_download_link(client, auth_headers, app):
    # First, add a file to the database
    with app.app_context():
        mongo.db.files.insert_one({
            'file_id': 'test_file',
            'filename': 'test.docx',
            'path': '/path/to/test.docx'
        })

    response = client.get('/download/test_file', headers=auth_headers)
    assert response.status_code == 200
    assert 'download_link' in response.json
    assert '/secure-download/' in response.json['download_link']


def test_generate_download_link_invalid_file_id(client, auth_headers, app):
    response = client.get('/download/invalid_file_id', headers=auth_headers)
    assert response.status_code == 404
    assert response.json['message'] == 'File not found'


def test_secure_download(client, auth_headers, app):
    # First, add a file to the database and generate a download token
    with app.app_context():
        mongo.db.files.insert_one({
            'file_id': 'test_file',
            'filename': 'test.docx',
            'path': 'tests/test.docx',
        })

        user_id = mongo.db.users.find_one({'email': 'test@example.com'})['_id']
        token = jwt.encode({
            'file_id': 'test_file',
            'user_id': str(user_id),
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5)
        }, app.config['SECRET_KEY'])

    response = client.get(f'/secure-download/{token}', headers=auth_headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == 'attachment; filename=test.docx'


def test_secure_download_expired_token(client, auth_headers, app):
    with app.app_context():
        user_id = mongo.db.users.find_one({'email': 'test@example.com'})['_id']
        token = jwt.encode({
            'file_id': 'test_file',
            'user_id': str(user_id),
            'exp': datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)
        }, app.config['SECRET_KEY'])

    response = client.get(f'/secure-download/{token}', headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Download link has expired'


def test_secure_download_invalid_token(client, auth_headers, app):
    response = client.get('/secure-download/invalid_token', headers=auth_headers)
    assert response.status_code == 400
    assert response.json['message'] == 'Invalid download link'


def test_secure_download_invalid_file_id(client, auth_headers, app):
    user_id = mongo.db.users.find_one({'email': 'test@example.com'})['_id']
    token = jwt.encode({
        'file_id': 'invalid_file_id',
        'user_id': str(user_id),
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5)
    }, app.config['SECRET_KEY'])

    response = client.get(f'/secure-download/{token}', headers=auth_headers)
    assert response.status_code == 404
    assert response.json['message'] == 'File not found'


def test_secure_download_invalid_user_id(client, auth_headers, app):
    with app.app_context():
        token = jwt.encode({
            'file_id': 'test_file',
            'user_id': 'invalid_user_id',
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5)
        }, app.config['SECRET_KEY'])

    response = client.get(f'/secure-download/{token}', headers=auth_headers)
    assert response.status_code == 403
    assert response.json['message'] == 'Unauthorized access'
