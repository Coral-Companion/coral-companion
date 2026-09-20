from sqlmodel import Session, select
import uuid

from app.domain.monitoring_session import MonitoringSession
from .database import get_session

class MonitoringSessionRepository:

    def save(self, monitoring_session: MonitoringSession) -> MonitoringSession:
        session = get_session()
        session.add(monitoring_session)
        session.commit()
        session.refresh(monitoring_session)
        return monitoring_session
    
    def find_all(self) -> list[MonitoringSession]:
        statement = (
            select(MonitoringSession)
            .order_by(MonitoringSession.timestamp.desc())
        )
        session: Session = get_session()
        return session.exec(statement).all()

    def find_by_id(self, id: str) -> MonitoringSession:
        session = get_session()
        return session.get(MonitoringSession, uuid.UUID(id))