from flask import Flask
from flask_bcrypt import Bcrypt

UPLOAD_PATH = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DB = "dojodating_db"

app = Flask(__name__)
app.config['UPLOAD_PATH'] = UPLOAD_PATH
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['UPLOAD_EXTENSIONS'] = ['.jpg','.png','.gif','.webp']
app.secret_key = "itsasecret"
bcrypt = Bcrypt(app)

from flask_app.controllers import user_controller,login_controller