from sqlmodel import SQLModel, Session, create_engine
from config import DATABASE_URL
print(f"✅ Connected to database: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=True)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session
