from pydantic import ConfigDict, Field
from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime

class MonitoringSessionResponse(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    name: str | None
    timestamp: datetime

    dive_site: str = Field(
        serialization_alias="diveSite"
    )

    observation_count: int = Field(
        serialization_alias="observationCount"
    )


class ObservationSummary(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    
    id: UUID;
    
    coral_name: str = Field(
        serialization_alias="coralName")
    
    monitoring_session_name: str = Field(
        serialization_alias="monitoringSessionSummary")
    
    monitoring_session_id: UUID = Field(
        serialization_alias="monitoringSessionId"
    )
    
    dive_site: str = Field(
        serialization_alias="diveSite"
    )
        
    observed_at: datetime = Field(
        serialization_alias="observedAt"
    )
    
    image_path: str = Field(
        serialization_alias="imagePath"
    )