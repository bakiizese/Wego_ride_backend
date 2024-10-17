from auth.authentication import Auth, _generate_uuid
from models import storage
from models.driver import Driver
new = Auth()
# new.register_user("Driver", username="bki", first_name="bereket", last_name="zeselassie", email="be@beki", phone_number=22, password_hash="passcode")
# new.verify_login("Driver", "be@beki", "passcode")

# user = new.create_reset_token("Driver", email="be@beki")
# print(f"in return last check {user}")
# new.update_password("Driver", reset_token="a5e76468-2b07-49f1-80a1-2ab4fda52df2", password="hello")

trip = storage.get('Trip', id="ead7b67d-c22b-41bf-a1a8-e17d64535330")
riders = trip.rider_id
for rider in riders:
    print(rider)