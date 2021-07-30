from flask_app import bcrypt
from flask_app.config.orm2 import Model,MtM,table,validator
import re
from datetime import date,datetime

@table
class User(Model):
    def __init__(self, **data):
#---------------------------attributes--------------------------#
        self.id = data.get('id')
        self.username = data.get('username')
        self.birthday = data.get('birthday')
        self.gender = data.get('gender')
        self.email = data.get('email')
        self.avatar = data.get('avatar')
        self.description = data.get('description')
        self.password = data.get('password')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
#---------------------------relationships-----------------------#
        self.likes = MtM("likes",liker=self,liked=User)
        self.liked_by = MtM("likes",liked=self,liker=User)
        self.passes = MtM("passes",passer=self,passed=User)
        self.matches = (Match.retrieve(matcher_id=self.id) + Match.retrieve(matched_id=self.id)).order_by(desc=True)
        self.seen_users = self.likes + self.passes
        self.messages = DirectMessage.retrieve(user_id=self.id)
#---------------------------------------------------------------#
    @property
    def age(self):
        return User.get_age(self.birthday)

    @staticmethod
    def get_age(born):#helper function to get age from birthday
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

#------------------------Validations-----------------------------#
    @validator("Username name must be at least 5 characters!")
    def username(val):
        return len(val) >= 2

    @validator("Must select a gender!")
    def gender(val):
        return val in ['male','female','nonbinary','other']

    @validator("You must be at least 18 years old!")
    def birthday(val):
        if val:
            return User.get_age(datetime.strptime(val,"%Y-%m-%d")) >= 18

    @validator("Must be a valid email!")
    def email(val):
        return re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$').match(val)

    @validator("Email is already in use!")
    def email(val):
        return not bool(User.retrieve(email=val).first())

    @validator("Password must be at least 8 characters!")
    def password(val):
        return len(val) >= 8

    @validator("Passwords must match!",match="password")
    def confirm_password(val,match):
        return val == match

    @validator("Invalid Email!")
    def login_email(val):
        return bool(User.retrieve(email=val).first())

    @validator("Invalid Password!",email="login_email")
    def login_password(val,email):
        user = User.retrieve(email=email).first()
        return user and bcrypt.check_password_hash(user.password,val)
#----------------------------------------------------------------#
from .direct_message_model import DirectMessage
from .match_model import Match