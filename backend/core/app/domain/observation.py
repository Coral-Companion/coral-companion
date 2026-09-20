from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column

from sqlalchemy.dialects.postgresql import JSONB

from sqlmodel import Field, SQLModel, Relationship

from app.embedding.embedding import EMBEDDING_DIMENSION
from app.domain.monitoring_session import MonitoringSession


class Observation(SQLModel, table=True):
    __tablename__ = "observations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    embedding: list[float] = Field(
        description="L2-normalized embedding vector produced by the embedding model.",
        sa_column=Column(Vector(EMBEDDING_DIMENSION), nullable=False),
    )

    monitoring_session_id: uuid.UUID = Field(
        foreign_key="monitoring_sessions.id",
        nullable=False,
    )
    
    monitoring_session: MonitoringSession = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
    })
    
    coral_name: str
    dive_site: str
    image_path: str
    image_filename: str
    image_width: int
    image_height: int
    cropped_image_path: str

    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
    )
    
    segments: dict | list | None = Field(
        default=None,
        sa_column=Column(JSONB)
    )
