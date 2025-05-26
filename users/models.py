import sqlmodel
from passlib.context import CryptContext

hashing = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto" )

class User(sqlmodel.SQLModel, table=True):
    __tablename__ = "usuarios"
    id: int = sqlmodel.Field(primary_key=True)
    email: str
    password: str
    first_name: str
    last_name: str
    role: str

    def set_password(self, password: str):
        self.password = hashing.hash(password)

    def verify_password(self, password: str):
        return hashing.verify(password, self.password)
