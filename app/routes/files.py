import os

from flask import Blueprint, request, jsonify, send_file, current_app
from app.services.files import upload_file, list_files, generate_download_link, download_file
from app.utils.decorators import token_required

bp = Blueprint('files', __name__)


@bp.route('/upload', methods=['POST'])
@token_required
def upload(current_user):
    if current_user['role'] != 'ops':
        return jsonify({'message': 'You are not allowed to upload files'}), 403
    result, status_code = upload_file(request.files.get('file', None), current_user)
    return jsonify(result), status_code


@bp.route('/files', methods=['GET'])
@token_required
def list_all_files(current_user):
    result = list_files()
    return jsonify(result), 200


@bp.route('/download/<file_id>', methods=['GET'])
@token_required
def download(current_user, file_id):
    result, status_code = generate_download_link(file_id, current_user)
    return jsonify(result), status_code


@bp.route('/secure-download/<token>', methods=['GET'])
@token_required
def secure_download(current_user, token):
    result, status_code = download_file(token, current_user)
    if result.get('message', None):
        return jsonify(result), status_code
    return send_file(str(os.path.join(current_app.config['ROOT_DIR'], result['path'])), as_attachment=True, download_name=result['filename'])
