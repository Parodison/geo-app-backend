from sqlmodel import SQLModel, create_engine, Session
from .settings import env
from users.models import *
from vehicles.models import *
from works.models import *

DATABASE_URL = env.database_url

engine = create_engine(DATABASE_URL, echo=False)

def get_db():
    with Session(bind=engine) as session:
        yield session
        
SQLModel.metadata.create_all(engine)