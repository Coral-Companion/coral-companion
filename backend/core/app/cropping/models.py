from dataclasses import dataclass
from app.domain.models import BoundingBox

import numpy as np

@dataclass
class CropResult:
    crop: np.ndarray

    content_box: BoundingBox
    square_box: BoundingBox

    padding: int