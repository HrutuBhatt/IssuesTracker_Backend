from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Step 1: Engine — the actual connection to the SQLite file
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}, 
)

# Step 2: SessionLocal — a factory to create DB sessions
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Step 3: Base — parent class for all ORM models
Base = declarative_base()


# Step 4: Dependency — FastAPI will inject this into routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()