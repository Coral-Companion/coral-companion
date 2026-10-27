from sqlmodel import Session, select, func
from uuid import UUID

from app.domain.observation import Observation
from app.domain.models import ObservationCandidate
from app.api.models import ObservationSummary
from app.domain.monitoring_session import MonitoringSession
from .database import get_engine

class ObservationRepository:

    def save(self, observation: Observation) -> Observation:
        with Session(get_engine()) as session:
            session.add(observation)
            session.commit()
            session.refresh(observation)
            return observation
    
    def find_similar(self, embedding: list[float], limit: int = 10) -> list[ObservationCandidate]:
        distance = Observation.embedding.cosine_distance(embedding)
        
        statement = (
            select(
                Observation,
                distance
            )
            .order_by(distance)
            .limit(limit)
        )
        with Session(get_engine()) as session:
            rows = session.exec(statement).all()        
            return [
                ObservationCandidate(
                    observation=observation,
                    distance=distance,
                    similarity=1-distance
                )
                for observation, distance in rows
            ]

    def find_by_id(self, id: UUID) -> Observation | None:
        with Session(get_engine()) as session:
            return session.get(Observation, id)
    
    def find_amount_per_session(self) -> dict[str, int]:
        statement = (
            select(
                Observation.monitoring_session_id,
                func.count(Observation.id)
            ).group_by(Observation.monitoring_session_id)
        )
        with Session(get_engine()) as session:
            observations_per_session = session.exec(statement).all()
        
        return {
            str(session_id): count
            for session_id, count in observations_per_session
        }
    
    def find_all_summaries(self) -> list[ObservationSummary]:
        statement = (
            select(
                Observation.id,
                Observation.coral_name,
                Observation.dive_site,
                MonitoringSession.timestamp.label("observed_at"),
                Observation.cropped_image_key.label("image_key"),
                func.concat(MonitoringSession.timestamp, " ", MonitoringSession.name).label("monitoring_session_name"),
                Observation.monitoring_session_id
            )
            .join(MonitoringSession)
            .order_by(Observation.coral_name)
        )
        with Session(get_engine()) as session:
            rows = session.exec(statement).mappings().all()

        return [
            ObservationSummary.model_validate(row)
            for row in rows 
        ]
        
    def find_summaries_by_ids(self, ids:list[UUID]) -> list[ObservationSummary]:
        statement = (
            select(
                Observation.id,
                Observation.coral_name,
                Observation.dive_site,
                MonitoringSession.timestamp.label("observed_at"),
                Observation.cropped_image_key.label("image_key"),
                func.concat(MonitoringSession.timestamp, " ", MonitoringSession.name).label("monitoring_session_name"),
                Observation.monitoring_session_id
            )
            .join(MonitoringSession)
            .where(Observation.id.in_(ids))
            .order_by(Observation.coral_name)
        )
        with Session(get_engine()) as session:
            rows = session.exec(statement).mappings().all()
        
        return [
            ObservationSummary.model_validate(row)
            for row in rows 
        ]
