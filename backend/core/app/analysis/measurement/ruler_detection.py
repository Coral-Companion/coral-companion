import numpy as np
import cv2
from pathlib import Path
from functools import reduce
import logging

from .models import RulerGeometry
from .zero_shot_ruler_segmentation_service import ZeroShotRulerSegmentationService
    
class RulerDetection:
    """
    <h3>Stage 1 of measurement pipeline</h3>
    Detects location of ruler and its long-axis orientation
    <br />
    <br />
    Produces a debug image with:
    <ul>
        <li>ruler contour</li>
        <li>center point</li>
        <li>long axis drawn through the ruler</li>
        <li>angle displayed</li>
        <li>bounding box</li>
    </ul>
    """    
    
    def __init__(self, *args, **kwargs):
        self.ruler_segmenter = ZeroShotRulerSegmentationService()
        self.logger = logging.getLogger(__name__)
        
    def detect_ruler(
            self,
            image: np.ndarray,
            name_for_debug: str | None = None,
        ) -> RulerGeometry:
        """
        Detects the ruler and derives its rough geometry.

        Returns:
            RulerGeometry containing the binary ruler mask and the geometry
            of its minimum-area bounding rectangle.
        """

        if image is None or image.size == 0:
            raise ValueError("Empty image passed to ruler detection.")

        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                "Ruler detection expects a BGR image with shape (H, W, 3)."
            )

        mask = self.ruler_segmenter.predict_ruler_mask(
            image,
            "a white measuring ruler . white scale slate",
        )

        if mask is None or mask.size == 0:
            raise ValueError("Ruler segmentation produced an empty mask.")

        if mask.shape != image.shape[:2]:
            raise ValueError(
                "Ruler segmentation returned a mask with invalid dimensions."
            )

        mask = np.where(mask > 0, 255, 0).astype(np.uint8)

        mask = self.find_largest_connected_component(mask)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            raise ValueError("No ruler contour detected.")

        # Find the largest segment because the segmenter sometimes
        # returns false positives. Including these in the bounding box will
        # result in a poor bounding box and angle. Visual inspections showed
        # that the ruler is the largest segment.
        ruler_contour = max(contours, key=cv2.contourArea)
        if len(ruler_contour) < 3:
            raise ValueError("Ruler contour contains too few points.")

        (center_x, center_y), (rect_width, rect_height), rect_angle = (
            cv2.minAreaRect(ruler_contour)
        )

        # minAreaRect gives us one rectangle side's orientation.
        # We want angle_degrees to always describe the LONG axis.
        if rect_width >= rect_height:
            width = rect_width
            height = rect_height
            angle_degrees = rect_angle
        else:
            width = rect_height
            height = rect_width
            angle_degrees = rect_angle + 90.0

        # Normalize the long-axis orientation: A ruler has no meaningful direction:
        # ---->   and   <---- represent the same physical orientation.
        # Therefore 180° differences are irrelevant.
        angle_degrees = ((angle_degrees + 90.0) % 180.0) - 90.0

        geometry = RulerGeometry(
            center=(float(center_x), float(center_y)),
            angle_degrees=float(angle_degrees),
            width=float(width),
            height=float(height),
            mask=mask,
        )
        
        self.logger.info(
            f"minAreaRect: "
            f"w={rect_width:.1f}, "
            f"h={rect_height:.1f}, "
            f"angle={rect_angle:.1f} "
            f"-> long-axis angle={angle_degrees:.1f}"
        )

        if name_for_debug:
            self._save_ruler_detection_debug_image(
                image=image,
                geometry=geometry,
                name=name_for_debug,
            )

        return geometry


    def find_largest_connected_component(self, mask: np.ndarray) -> np.ndarray:
        """
        Find the largest connected foreground component in a binary mask.

        Args:
            mask: Binary mask where foreground is non-zero.

        Returns:
            Binary mask containing only the largest connected component.
        """
        binary_mask = (mask > 0).astype(np.uint8)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary_mask,
            connectivity=8,
        )

        # Label 0 is the background.
        if num_labels <= 1:
            return np.zeros_like(binary_mask)

        # Ignore background and find largest foreground component.
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])

        return (labels == largest_label).astype(np.uint8) * 255

    def _save_ruler_detection_debug_image(
        self,
        image: np.ndarray,
        geometry: RulerGeometry,
        name: str,
    ) -> None:
        debug = image.copy()

        contours, _ = cv2.findContours(
            geometry.mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if contours:
            cv2.drawContours(
                debug,
                contours,
                -1,
                (0, 0, 255),
                2,
            )
            cv2.putText(debug,
                f"angle: {geometry.angle_degrees}",
                (100, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2
            )

        rect = (
            geometry.center,
            (geometry.width, geometry.height),
            geometry.angle_degrees,
        )

        box = cv2.boxPoints(rect).astype(np.int32)

        cv2.polylines(
            debug,
            [box],
            isClosed=True,
            color=(255, 0, 0),
            thickness=2,
        )

        output_path = (
            Path("test/analysis/measurement/debug")
            / f"{name}_stage_1_ruler_detection.png"
        )
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not cv2.imwrite(str(output_path), debug):
            raise IOError(
                f"Failed to write ruler detection debug image: {output_path}"
            )

        self.logger.info(
            "[RULER DETECTION]"
            f" center={geometry.center}"
            f" angle={geometry.angle_degrees:.2f}°"
            f" width={geometry.width:.1f}px"
            f" height={geometry.height:.1f}px"
            f" mask_pixels={np.count_nonzero(geometry.mask)}"
        )
        self.logger.info(f"[RULER DETECTION] debug image: {output_path}")