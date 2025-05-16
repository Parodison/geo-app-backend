from sqlmodel import create_engine, Session
from .settings import env

DATABASE_URL = env.database_url

engine = create_engine(DATABASE_URL, echo=False)

def get_db():
    with Session(bind=engine) as session:
        yield session