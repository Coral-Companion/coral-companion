from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO
import numpy as np

from app.segmentation.models import SegmentationResult


class SegmentationProvider(ABC):
    @abstractmethod
    async def segment(
        self,
        image: bytes,
        image_filename: str,
        layers: int = 0,
        points_per_side: int = 10,
        points_per_batch: int = 32,
    ) -> SegmentationResult:
        ...
