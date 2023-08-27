import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get("HOST")
port = os.environ.get("POSTGRES_PORT")
user = os.environ.get("POSTGRES_USER")
name = os.environ.get("POSTGRES_NAME")
password = os.environ.get("POSTGRES_PASSWORD")

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    """
        The get_db function is a context manager that returns the database session.
        It also ensures that the connection to the database is closed after each request.

        :return: A database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
