import bcrypt
from models import storage
from models.driver import Driver
from models.rider import Rider
from models.admin import Admin
import datetime
import uuid
import jwt

classes = {"Driver": Driver, 
           "Rider": Rider,
           "Admin": Admin}

SECRET_KEY = 'wego_rider_service_secret_key'

class Auth:
    '''Authentication class to register, verify, change password'''
    def register_user(self, cls, **kwargs):
        '''register new user if phone_number and email dont exist in db'''
        user0 = storage.get_all(cls, username=kwargs['username'])
        user1 = storage.get_all(cls, email=kwargs['email'])
        user2 = storage.get_all(cls, phone_number=kwargs['phone_number'])
        if user0:
            print("** username already exists **")
            return '** username already exists **', False  
        if user1:
            print("** email already exists **")
            return '** email already exists **', False
        if user2:
            print("** phone number already exists **")
            return '** phone number already exists **', False
        kwargs["password_hash"] = _hash_password(kwargs['password_hash'])

        user = classes[cls](**kwargs)
        user.save()
        print(user.id)
        return user.id, True


    def update_password(self, cls, reset_token, password):
        '''update password using reset_token'''
        user = storage.get(cls, reset_token=reset_token)
        if user:
            password_hash = _hash_password(password)
            storage.update(cls, user.id, password_hash=password_hash)
            storage.update(cls, user.id, reset_token=None)
            return True
        else:
            return False
        

    def verify_login(self, cls, email, password):
        '''verify login if email and password are correct'''
        user = storage.get(cls, email=email)
        if user:
            if self.verify_password(password, user):
               jwt_token = _generate_jwt(user)
               return '** login verified **', jwt_token
            else:
                return '** incorrect password **', False
        else:
            return '** email doesn\'t exist **', False

    def verify_password(self, login_password, saved_password):
        '''check if the login password is the same with saved_password'''
        return bcrypt.checkpw(login_password.encode("utf-8"), saved_password.password_hash.encode("utf-8"))

    def create_reset_token(self, cls,  email):
        '''create a token for updateing password'''
        user = storage.get(cls, email=email)
        reset_token = None
        if user:
            reset_token = _generate_uuid()
        storage.update(cls, user.id, reset_token=reset_token)
        return reset_token

def _hash_password(password):
    '''encrypt string password to binary using bcrypt'''
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _generate_uuid():
    '''generate random string for token'''
    token = str(uuid.uuid4())
    return token

def _generate_jwt(user):
    '''generate jwt token using secret key and payload'''
    token_payload = {
        'sub': user.id,
        'role': user.__class__.__name__,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(weeks=4)
        }
    jwt_token = jwt.encode(token_payload, SECRET_KEY,  algorithm='HS256')
    return jwt_token
    