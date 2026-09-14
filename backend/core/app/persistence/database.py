from sqlmodel import create_engine, Session
from sqlmodel import SQLModel
from dotenv import load_dotenv
import os
load_dotenv()

# Imports necessary for sqlmodel
from app.domain.monitoring_session import MonitoringSession
from app.domain.observation import Observation

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    echo=True,
)

def get_session() -> Session:
    return Session(engine)