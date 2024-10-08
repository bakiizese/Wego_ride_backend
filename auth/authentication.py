import bcrypt
from models import storage
from models.driver import Driver
from models.rider import Rider
import uuid

classes = {"Driver": Driver, 
           "Rider": Rider}

class Auth:
    def register_user(self, cls, **kwargs):
        user1 = storage.get_all(classes[cls], email=kwargs['email'])
        user2 = storage.get_all(classes[cls], phone_number=kwargs['phone_number'])
        if user1:
            print("** email already exists **")
            return False
        if user2:
            print("** phone number already exists **")
            return False
        kwargs["password_hash"] = _hash_password(kwargs['password_hash'])

        user = classes[cls](**kwargs)
        user.save()
        print(user.id)


    def update_password(self, cls, reset_token, password):
        user = storage.get(cls, reset_token=reset_token)
        if user:
            password_hash = _hash_password(password)
            storage.update(cls, user.id, password_hash=password_hash)
            storage.update(cls, user.id, reset_token=None)
            return True
        else:
            return False
        

    def verify_login(self, cls, email, password):
        user = storage.get(classes[cls], email=email)
        if user:
            if bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
               return True
            else:
                return False
        else:
            return False


    def create_reset_token(self, cls,  email):
        user = storage.get(classes[cls], email=email)
        if user:
            reset_token = _generate_uuid()
        storage.update(cls, user.id, reset_token=reset_token)
        return reset_token


def _hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _generate_uuid():
    token = str(uuid.uuid4())
    return token