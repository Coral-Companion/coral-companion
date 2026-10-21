from sqlmodel import create_engine, Session
from sqlmodel import SQLModel
from sqlalchemy.engine import make_url
import os
import psycopg

from dotenv import load_dotenv
load_dotenv()

# Imports necessary for sqlmodel
from app.domain.monitoring_session import MonitoringSession
from app.domain.observation import Observation

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )
print("Database driver:", make_url(DATABASE_URL).drivername)
engine = create_engine(
    DATABASE_URL,
    echo=True,
    module=psycopg
)

def get_session() -> Session:
    return Session(engine)