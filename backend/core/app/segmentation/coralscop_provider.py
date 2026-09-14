from __future__ import annotations

import logging
from pathlib import Path

from app.domain.models import BoundingBox, Point, Segment
import cv2
import numpy as np
import torch

from app.segmentation.models import SegmentationResult
from app.segmentation.segmentation_provider import SegmentationProvider
from third_party.coralscop.segment_anything import (
    SamAutomaticMaskGenerator,
    sam_model_registry,
)
from app.segmentation.fixture_exporter import export_segmentation_fixture
from app.utils.performance_profiler import performance_stage, log_memory

logger = logging.getLogger(__name__)

class CoralScopProvider(SegmentationProvider):
    """Thin wrapper around CoralSCOP that returns the application's typed segment models."""

    def __init__(self, checkpoint_path: str | None = None, model_type: str = "vit_b") -> None:
        if checkpoint_path is None:
            checkpoint_path = (
                Path(__file__).resolve().parents[2]
                / "third_party"
                / "coralscop"
                / "checkpoints"
                / "vit_b_coralscop.pth"
            )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"[Segmentation] Using provider: CoralSCOP")
        logger.info(f"[Segmentation] Using device: {self.device}")

        sam = sam_model_registry[model_type](checkpoint=str(checkpoint_path))
        sam.to(device=self.device)

        with performance_stage("create mask generator"):
            self.mask_generator = SamAutomaticMaskGenerator(
                model=sam,
                points_per_side=10,
                pred_iou_thresh=0.75,
                stability_score_thresh=0.75,
                crop_n_layers=0,
                crop_n_points_downscale_factor=2,
                min_mask_region_area=100,
                points_per_batch=32
            )

    def segment(self, image: np.ndarray | None, image_filename: str) -> SegmentationResult:
        if image is None:
            raise ValueError("Image is None.")
        if len(image.shape) != 3:
            raise ValueError("Expected BGR image.")

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        masks = self.mask_generator.generate(rgb)

        with performance_stage("putting together segments"):
            segments: list[Segment] = []
            for index, mask_record in enumerate(masks):
                segmentation = mask_record.get("segmentation")
                bbox = mask_record.get("bbox", [0, 0, 0, 0])
                polygon_points = []
                if isinstance(segmentation, np.ndarray):
                    mask = segmentation
                    mask = (mask > 0).astype(np.uint8) * 255
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                    if contours:
                        contour = max(contours, key=cv2.contourArea)
                        polygon_points = [Point(int(x), int(y)) for x, y in contour.reshape(-1, 2)]

                segments.append(
                    Segment(
                        id=index,
                        polygon=polygon_points,
                        bbox=BoundingBox(
                            x=int(bbox[0]),
                            y=int(bbox[1]),
                            width=int(bbox[2]),
                            height=int(bbox[3]),
                        ),
                        predictedIoU=float(mask_record.get("predicted_iou", 0.0)),
                        stabilityScore=float(mask_record.get("stability_score", 0.0)),
                    )
                )

            height, width = image.shape[:2]
        
        with performance_stage("creating fixture"):
            # TODO: This doesn't really belong here but for building a devleopment dataset it is handy. Remove or comment before releas
            try:
                export_segmentation_fixture(image, image_filename, masks)
            except Exception as e:
                logger.exception(f"[Segmentation] Failed writing fixture. {str(e)}")

        return SegmentationResult(
            image_width=int(width),
            image_height=int(height),
            segments=segments,
        )
