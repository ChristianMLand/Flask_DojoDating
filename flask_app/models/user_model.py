from flask_app import bcrypt
from flask_app.config.orm2 import Model,MtM,table
import re
from datetime import date,datetime

@table
class User(Model):
    def __init__(self, **data):
#----------------attributes--------------------#
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
#---------------relationships-------------------#
        self.likes = MtM("likes",liker=self,liked=User)
        self.liked_by = MtM("likes",liked=self,liker=User)
        self.passes = MtM("passes",passer=self,passed=User)
        self.mutuals = self.likes.intersect(self.liked_by._query)
        self.seen_users = self.likes + self.passes
#-----------------------------------------------#
    @property
    def age(self):
        return User.get_age(self.birthday)

    @staticmethod
    def get_age(born):#helper function to get age from birthday
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

#----------------------Validations-----------------------------#
@User.validator("Username name must be at least 5 characters!")
def username(val):
    return len(val) >= 2

@User.validator("Must select a gender!")
def gender(val):
    return val in ['male','female','nonbinary','other']

@User.validator("You must be at least 18 years old!")
def birthday(val):
    if val:
        return User.get_age(datetime.strptime(val,"%Y-%m-%d")) >= 18

@User.validator("Must be a valid email!")
def email(val):
    return re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$').match(val)

@User.validator("Email is already in use!")
def email(val):
    return not bool(User.retrieve(email=val).first())

@User.validator("Password must be at least 8 characters!")
def password(val):
    return len(val) >= 8

@User.validator("Passwords must match!",match="password")
def confirm_password(val,match):
    return val == match

@User.validator("Invalid Email!")
def login_email(val):
    return bool(User.retrieve(email=val).first())

@User.validator("Invalid Password!",email="login_email")
def login_password(val,email):
    user = User.retrieve(email=email).first()
    return user and bcrypt.check_password_hash(user.password,val)

# @User.validator("Avatar must be an image!")
# def avatar(val):#TODO
#     return True
#----------------------------------------------------------------#