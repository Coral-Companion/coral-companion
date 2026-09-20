from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class RulerGeometry:
    center: tuple[float, float]
    angle_degrees: float
    width: float
    height: float
    mask: np.ndarray


@dataclass(frozen=True)
class RotatedRuler:
    """
    Result of rotating and cropping a detected ruler.

    image:
        Cropped original image with the ruler's long axis horizontal.

    mask:
        Cropped binary ruler mask in the same coordinate system as image.

    crop:
        Crop rectangle in the rotated full-image coordinate system:
        (x, y, width, height).
    """
    image: np.ndarray
    mask: np.ndarray
    crop: tuple[int, int, int, int]


@dataclass(frozen=True)
class TickSignals:
    signal: np.ndarray
    threshold: float

# Only for internal use in tick_detection
@dataclass(frozen=True)
class TickSignalScore:
    score: float
    peak_count: int
    coefficient_of_variation: float

@dataclass(frozen=True)
class TickPositions:
    positions: np.ndarray
    strengths: np.ndarray

# Only for internal use in scale estimation
@dataclass(frozen=True)
class ScaleFit:
    pixels_per_mm: float
    intercept: float
    supporting_ticks: np.ndarray
    derived_ticks: np.ndarray
    residual: float

@dataclass(frozen=True)
class RulerScale:
    pixels_per_mm: float
    confidence: float
    supporting_ticks: np.ndarray
    spacing_residual: float

    
@dataclass(frozen=True)
class CoralMeasurement:
    feret_cm: float
    geodesic_cm: float
    px_per_cm: float
    