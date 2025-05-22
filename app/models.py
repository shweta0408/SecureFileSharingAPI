from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    def __init__(self, email, password, role='client', verified=False):
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.role = role
        self.verified = verified

    @staticmethod
    def check_password(password_hash, password):
        return check_password_hash(password_hash, password)

    def save(self):
        return mongo.db.users.insert_one({
            'email': self.email,
            'password': self.password_hash,
            'role': self.role,
            'verified': self.verified
        })


class File:
    def __init__(self, file_id, filename, path, uploaded_by):
        self.file_id = file_id
        self.filename = filename
        self.path = path
        self.uploaded_by = uploaded_by

    def save(self):
        return mongo.db.files.insert_one({
            'file_id': self.file_id,
            'filename': self.filename,
            'path': self.path,
            'uploaded_by': self.uploaded_by
        })
