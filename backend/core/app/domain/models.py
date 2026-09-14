from dataclasses import dataclass
from typing import List
from app.domain.observation import Observation

@dataclass(slots=True)
class Point:
    x: int
    y: int


@dataclass(slots=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    
    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> tuple[float, float]:
        return (
            self.x + self.width / 2,
            self.y + self.height / 2,
        )

@dataclass(slots=True)
class Segment:
    id: int
    polygon: List[Point]
    bbox: BoundingBox
    predictedIoU: float
    stabilityScore: float
    
    def score(self) -> float :
        area = self.bbox.width * self.bbox.height
        return area * self.predictedIoU
    
@dataclass(slots=True)
class ObservationCandidate:
    observation: Observation
    distance: float
    similarity: float

@dataclass(slots=True)
class Metric:
    id: str
    value: float
    changePercentage: float | None
