import bcrypt
from models import storage
from models.driver import Driver
from models.rider import Rider
import uuid

classes = {"Driver": Driver, 
           "Rider": Rider}

class Auth:
    def register_user(self, cls, username, first_name, last_name, email, phone_number, password):
        user1 = storage.get_all(classes[cls], email=email)
        user2 = storage.get_all(classes[cls], phone_number=phone_number)
        if user1:
            print("** email already exists **")
            return False
        if user2:
            print("** phone number already exists **")
            return False
        password_hash = _hash_password(password)
        new_dict = {"username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone_number": phone_number,
                    "password_hash": password_hash}
        user = classes[cls](**new_dict)
        user.save()
        print(user.id)

    def update_password(self, reset_token, password):
        pass
    
    def verify_login(self, cls, email, password):
        user = storage.get(classes[cls], email=email)
        if user:
            if bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
                print("verified")
            else:
                print("incorrect pasword")
        else:
            print("user not found")

    def create_reset_token(self, cls,  email, new_password):
        user = storage.get(classes[cls], email=email)
        if user:
            reset_token = _generate_uuid()
            

    

def _hash_password(password):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    
def _generate_uuid():
    return str(uuid.uuid4())