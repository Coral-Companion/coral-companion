import json
from datetime import datetime
from typing import List, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models import Segment, BoundingBox, Point, ObservationCandidate
from app.domain.monitoring_session import MonitoringSession
from app.segmentation.models import SegmentationResult

class MonitoringSessionCreate(BaseModel):
    name: str
    timestamp: datetime
    diveSite: str

    def to_domain(self) -> MonitoringSession:
        return MonitoringSession(
            name=self.name,
            timestamp=self.timestamp,
            dive_site=self.diveSite
        )

class ObservationComparisonRequest(BaseModel):
    observationIds: List[UUID]

def parse_segments_form_data(segments_json_str: str) -> List[Segment]:
    """
    Helper to parse stringified JSON from multipart/form-data into Domain models.
    """
    try:
        payload = json.loads(segments_json_str)
        segments_data = payload.get("selectedSegments", [])
        return [
            Segment(
                id=seg["id"],
                bbox=BoundingBox(
                    x=seg["bbox"]["x"],
                    y=seg["bbox"]["y"],
                    width=seg["bbox"]["width"],
                    height=seg["bbox"]["height"],
                ),
                polygon=[Point(x=p[0], y=p[1]) for p in seg["polygon"]],
                predictedIoU=seg["predictedIoU"],
                stabilityScore=seg["stabilityScore"],
            )
            for seg in segments_data
        ]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError(f"Invalid segments payload provided: {str(e)}")


class ImageDimensionsResponse(BaseModel):
    height: int
    width: int

class BoundingBoxResponse(BaseModel):
    x: int
    y: int
    width: int
    height: int

class SegmentResponse(BaseModel):
    id: str
    bbox: BoundingBoxResponse
    polygon: List[Tuple[int, int]]
    predictedIoU: float
    stabilityScore: float

class ObservationCandidateResponse(BaseModel):
    id: UUID
    coralId: UUID
    coralName: str
    monitoringSessionDate: datetime
    visualSimilarity: float
    diveSite: str
    imageUrl: str

    @classmethod
    def from_domain(cls, candidate: ObservationCandidate) -> "ObservationCandidateResponse":
        return cls(
            id=candidate.observation.id,
            coralId=candidate.observation.id,
            coralName=candidate.observation.coral_name,
            monitoringSessionDate=candidate.observation.monitoring_session.timestamp,
            visualSimilarity=candidate.similarity,
            diveSite=candidate.observation.dive_site,
            imageUrl=candidate.observation.cropped_image_path
        )

class ImageUploadResponse(BaseModel):
    image: ImageDimensionsResponse
    segments: List[SegmentResponse]
    observationCandidates: List[ObservationCandidateResponse]

    @classmethod
    def from_domain(cls, result: SegmentationResult, candidates: List[ObservationCandidate]) -> "ImageUploadResponse":
        return cls(
            image=ImageDimensionsResponse(height=result.image_height, width=result.image_width),
            segments=[
                SegmentResponse(
                    id=str(segment.id),
                    bbox=BoundingBoxResponse(
                        x=segment.bbox.x, y=segment.bbox.y,
                        width=segment.bbox.width, height=segment.bbox.height
                    ),
                    polygon=[(point.x, point.y) for point in segment.polygon],
                    predictedIoU=segment.predictedIoU,
                    stabilityScore=segment.stabilityScore
                )
                for segment in result.segments
            ],
            observationCandidates=[
                ObservationCandidateResponse.from_domain(c) for c in candidates
            ]
        )

class IdentifyResponse(BaseModel):
    candidates: List[ObservationCandidateResponse]

class ConfirmCoralResponse(BaseModel):
    observationId: UUID

class CreateMonitoringSessionResponse(BaseModel):
    monitoringSessionId: UUID