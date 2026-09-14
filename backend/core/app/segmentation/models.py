from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import Segment


@dataclass(slots=True)
class SegmentationResult:
    image_width: int = 0
    image_height: int = 0
    segments: list[Segment] = field(default_factory=list)
