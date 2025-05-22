import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGO_URI = os.getenv('MONGO_URI')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
    ALLOWED_EXTENSIONS = {'pptx', 'docx', 'xlsx'}
    ROOT_DIR = os.path.abspath(os.curdir)
    BASE_URL = os.getenv('BASE_URL') or 'http://127.0.0.1:5000/'
    SMTP2GO_API_KEY = os.getenv('SMTP2GO_API_KEY')
    SMTP2GO_SENDER = os.getenv('SMTP2GO_SENDER')
