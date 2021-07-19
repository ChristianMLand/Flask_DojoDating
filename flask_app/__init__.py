from flask import Flask
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO


UPLOAD_PATH = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DB = "dojodating_db"
MESSAGE_COUNT = 8

app = Flask(__name__)
app.config['UPLOAD_PATH'] = UPLOAD_PATH
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['UPLOAD_EXTENSIONS'] = ['.jpg','.png','.gif','.webp']
app.secret_key = "itsasecret"

bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins='*')

from flask_app.controllers import user_controller,login_controller,direct_message_controller