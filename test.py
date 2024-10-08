from auth.authentication import Auth

new = Auth()
# new.register_user("Driver", "beki", "bereket", "zeselassie", "baki@baki", 912232, "pascode123")
new.verify_login("Driver", "baki@baki", "pascode123")
