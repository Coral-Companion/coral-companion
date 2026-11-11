from sqlmodel import Session, select
import uuid

from app.domain.survey import Survey
from .database import get_engine

class SurveyRepository:

    def save(self, survey: Survey) -> Survey:
        with Session(get_engine()) as session:
            session.add(survey)
            session.commit()
            session.refresh(survey)
            return survey
    
    def find_all(self) -> list[Survey]:
        statement = (
            select(Survey)
            .order_by(Survey.timestamp.desc())
        )
        with Session(get_engine()) as session:
            return list(session.exec(statement).all())

    def find_by_id(self, id: str) -> Survey | None:
        with Session(get_engine()) as session:
            return session.get(Survey, uuid.UUID(id))