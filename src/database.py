from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import accounting_settings


engine = create_engine(str(accounting_settings.pg_dsn))

Session = sessionmaker(
    engine,
    autocommit=False,
    autoflush=False
)


def get_session() -> Session:
    session = Session()
    try:
        yield session
    finally:
        session.close()


"""
# in PyCharm run in Python Console (before make sure 'src' is configured as working dir to access .env):
from src.database import engine
from src.tables import Base
Base.metadata.create_all(engine)
"""