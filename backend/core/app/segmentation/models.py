from __future__ import annotations

from pydantic import BaseModel, Field
from app.domain.models import Segment

class SegmentationResult(BaseModel):
    image_width: int = 0
    image_height: int = 0
    segments: list[Segment] = Field(default_factory=list)