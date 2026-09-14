from dataclasses import dataclass, field

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

@dataclass(slots=True)
class Segment:
    id: int
    polygon: list[Point]
    bbox: BoundingBox
    predictedIoU: float
    stabilityScore: float

@dataclass(slots=True)
class SegmentationResult:
    image_width: int = 0
    image_height: int = 0
    # TODO: check if the field(default_factory is really necessary)
    segments: list[Segment] = field(default_factory=list)
