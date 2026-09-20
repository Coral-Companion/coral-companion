from app.domain.models import Segment
from app.domain.observation import Observation
import numpy as np

from dataclasses import dataclass


@dataclass(slots=True)
class IdentifyResult:
    crop: np.ndarray
    masked_image: np.ndarray
    embedding: list[float]
    selected_segments: list[Segment]


@dataclass(slots=True)
class IdentifyRequest:
    image: np.ndarray
    selected_segments: list[Segment]
    
@dataclass(slots=True)
class ConfirmRequest:
    image: np.ndarray
    selected_segments: list[Segment]
    dive_site: str
    coral_name: str
    monitoring_session_id: str
    
@dataclass(slots=True)
class ConfirmResult:
    observation: Observation