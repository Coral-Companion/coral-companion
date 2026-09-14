from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.segmentation.models import SegmentationResult


class SegmentationProvider(ABC):
    @abstractmethod
    def segment(self, image: np.ndarray | None, image_filename: str) -> SegmentationResult:
        ...
