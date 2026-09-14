from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import List

from app.domain.models import BoundingBox, Point, Segment
import numpy as np

from app.segmentation.models import SegmentationResult
from app.segmentation.segmentation_provider import SegmentationProvider

logger = logging.getLogger(__name__)


class FixtureProvider(SegmentationProvider):
    def __init__(self, fixtures_dir: str | os.PathLike[str] | None = None):
        base_dir = Path(__file__).resolve().parents[2]
        self.fixtures_dir = (
            Path(fixtures_dir)
            if fixtures_dir is not None
            else base_dir / "dev_fixtures"
        )
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

    def _get_fixture_json_path(self, image_filename: str) -> Path:
        image_path = next(
            self.fixtures_dir.rglob(image_filename),
            None,
        )

        if image_path is None:
            raise FileNotFoundError(
                f"Image fixture not found: {image_filename}"
            )

        fixture_dir = image_path.parent

        json_path = fixture_dir / f"{image_path.stem}.json"

        if not json_path.exists():
            raise FileNotFoundError(
                f"JSON fixture not found for image: {image_path}"
            )

        return json_path

    def segment(
        self,
        image: np.ndarray | None,
        image_filename: str,
    ) -> SegmentationResult:

        json_file = self._get_fixture_json_path(image_filename)

        with json_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        
        segments_payload = payload.get("segments", [])

        segments: List[Segment] = []

        for segment_payload in segments_payload:
            polygon = [
                Point(
                    x=int(point[0]),
                    y=int(point[1]),
                )
                for point in segment_payload.get("polygon", [])
            ]

            bbox_payload = segment_payload.get("bbox", {})

            bbox = BoundingBox(
                x=int(bbox_payload.get("x", 0)),
                y=int(bbox_payload.get("y", 0)),
                width=int(bbox_payload.get("width", 0)),
                height=int(bbox_payload.get("height", 0)),
            )

            segments.append(
                Segment(
                    id=int(segment_payload.get("id", 0)),
                    polygon=polygon,
                    bbox=bbox,
                    predictedIoU=float(
                        segment_payload.get("predictedIoU", 0.0)
                    ),
                    stabilityScore=float(
                        segment_payload.get("stabilityScore", 0.0)
                    ),
                )
            )
            
        image_payload = payload.get("image", {})
        
        return SegmentationResult(
            image_width=int(image_payload.get("width", 0)),
            image_height=int(image_payload.get("height", 0)),
            segments=segments,
        )