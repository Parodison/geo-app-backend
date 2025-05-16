import jwt
from .settings import env
from datetime import datetime, timedelta, timezone

class Authentication:
    def __init__(self):
        self.secret_key = env.secret_key
        self.algorithm = "HS256"
        self.access_token_expiration = timedelta(minutes=30)
        self.refresh_token_expiration = timedelta(days=30)

    def create_refresh_token(self, data: dict) -> str:
        payload = {
            "exp": datetime.now(timezone.utc) + self.refresh_token_expiration,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            **data,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, data: dict) -> str:
        payload = {
            "exp": datetime.now(timezone.utc) + self.access_token_expiration,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            **data,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    

auth = Authentication()
