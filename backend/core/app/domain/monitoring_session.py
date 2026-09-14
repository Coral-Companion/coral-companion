from __future__ import annotations
import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel
from pydantic import PrivateAttr


class MonitoringSession(SQLModel, table=True):
    __tablename__ = "monitoring_sessions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    
    name: str = Field(default="", sa_column_kwargs={"server_default": ""})
    timestamp: datetime
    dive_site: str = Field(default="", sa_column_kwargs={"server_default": ""})
    