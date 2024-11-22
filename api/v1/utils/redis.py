from flask import current_app


class Redis:
    def __init__(self):
        self.redis = current_app.extensions["redis"]
        if not self.redis:
            raise RuntimeError("Redis extension is not configured in Flask.")

    def jwt_blacklist(self, jwt_token, exp):
        try:
            self.redis.setex(jwt_token, exp, "blacklisted")
        except Exception as e:
            raise Exception(e)

    def check_jwt_blacklist(self, jwt_token):
        return self.redis.exists(jwt_token) == 1
