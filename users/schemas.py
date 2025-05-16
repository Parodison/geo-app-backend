from typing import Optional
from pydantic import BaseModel

class UserSchema(BaseModel):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
