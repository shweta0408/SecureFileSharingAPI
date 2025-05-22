from app.models import File
from app import mongo
from flask import current_app
import os
import uuid
from werkzeug.utils import secure_filename
import jwt
import datetime
import magic


def get_file_type(file_path):
    mime = magic.from_file(file_path, mime=True)
    mime_to_ext = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx'
    }
    return mime_to_ext.get(mime)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def upload_file(file, current_user):
    if not file or file.filename == '':
        return {'message': 'No file selected for uploading'}, 400
    if file and allowed_file(file.filename):
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)

        if not os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], file_id[:2])):
            os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], file_id[:2]))
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id[:2], file_id[2:] + '_' + filename)
        file.save(file_path)

        file_type = get_file_type(file_path)
        if not file_type:
            os.remove(file_path)
            return {'message': 'Invalid file content. Allowed file types are pptx, docx, xlsx'}, 400

        new_file = File(file_id, filename, file_path, str(current_user['_id']))
        new_file.save()
        return {'message': 'File successfully uploaded', 'file_id': file_id}, 201
    else:
        return {'message': 'Allowed file types are pptx, docx, xlsx'}, 400


def list_files():
    files = mongo.db.files.find()
    return [{'file_id': file['file_id'], 'filename': file['filename']} for file in files]


def generate_download_link(file_id, current_user):
    file = mongo.db.files.find_one({'file_id': file_id})
    if not file:
        return {'message': 'File not found'}, 404

    download_token = jwt.encode({
        'file_id': file_id,
        'user_id': str(current_user['_id']),
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=60)
    }, current_app.config['SECRET_KEY'])

    download_link = current_app.config['BASE_URL'] + f"/secure-download/{download_token}"
    return {'download_link': download_link, 'message': 'Link successfully generated. Valid for 60 minutes.'}, 200


def download_file(token, current_user):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        if str(current_user['_id']) != data['user_id']:
            return {'message': 'Unauthorized access'}, 403

        file = mongo.db.files.find_one({'file_id': data['file_id']})
        if not file:
            return {'message': 'File not found'}, 404

        return {'path': file['path'], 'filename': file['filename']}, 200
    except jwt.ExpiredSignatureError:
        return {'message': 'Download link has expired'}, 400
    except jwt.InvalidTokenError:
        return {'message': 'Invalid download link'}, 400
