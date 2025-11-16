from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import Config

engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

# Simple context manager for sessions
class SessionContext:
    def __enter__(self):
        self.session = SessionLocal()
        return self.session

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
        finally:
            self.session.close()

# NEW: Function to check database connectivity
def check_db_health():
    """Attempts to connect to the DB and execute a simple query."""
    try:
        with SessionContext() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False