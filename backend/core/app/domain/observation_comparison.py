from sqlmodel import SQLModel

from app.domain.models import Metric
from app.api.models import ObservationSummary

class ObservationComparison(SQLModel):
    
    baseline: ObservationSummary | None
    observation: ObservationSummary
    metrics: list[Metric]