import cv2
import numpy as np
import logging
from pathlib import Path

from .ruler_detection import RulerDetection
from .ruler_rotation import RulerRotation
from .tick_detection import TickDetection
from .tick_positioning import TickPositioning
from .scale_estimation import ScaleEstimation
from .models import CoralMeasurement
from app.domain.models import Segment
from app.vision.vision_service import VisionService

class CoralMeasurementService:
    """
    Estimate coral dimensions from an image containing a metric ruler.

    The ruler is first segmented, rotated so its long axis is horizontal,
    and then analysed along that axis.

    <h3>Assumptions:</h3>
        Relevant parts of the ruler are of a bright gray/silver/slate color.
        Ruler is metric.
        Metric ticks are perpendicular to the ruler's long axis.

    <h3>Stages of measurement:</h3>
    Identify ruler and metric units:
    <ol>
        <li>Detect ruler and its rotation</li>
        <li>Rotate ruler mask</li>
        <li>Detect the signal of the (now) vertical ticks (strength and size)</li>
        <li>Interpret the detected signals of the ticks</li>
        <li>Estimate the ruler scale (px / mm or px / cm)</li>
    </ol>
    Measure coral:
    <ol>
        <li>Find the longest feret diameter</li>
        <li>Approximate geodesic skeleton</li>
        <li>Use metric units to calculate sizes</li>
    <ol>
    """


    def __init__(
        self,
    ) -> None:
        self.ruler_detection = RulerDetection()
        self.ruler_rotation = RulerRotation()
        self.tick_detection = TickDetection(threshold_percentile=95)
        self.tick_positioning = TickPositioning()
        self.scale_estimation = ScaleEstimation()
        self.vision_service = VisionService()
        self.logger = logging.getLogger(__name__)
        
    def measure_coral(self,
            image: np.ndarray,
            coral_mask: Segment,
            name_for_debug: str | None = None
        ) -> CoralMeasurement:
        px_per_cm = self.estimate_px_per_cm(image, name_for_debug)
        self.logger.info(f"pixels per cm: {px_per_cm}")
        
        
        # determine geodesic skeleton segments
        # calculate feret diameter length
        feret = self.determine_feret_diameter(image, coral_mask, px_per_cm, name_for_debug)
        
        # put together image and stats result
        return CoralMeasurement(
            px_per_cm=px_per_cm,
            feret_cm=feret,
            geodesic_cm=0
        )


    def estimate_px_per_cm(self, image: np.ndarray, name_for_debug: str | None = None) -> float:
        ruler_geometry = self.ruler_detection.detect_ruler(image, name_for_debug=name_for_debug)
        rotated_ruler = self.ruler_rotation.rotate_ruler(image, ruler_geometry.mask, ruler_geometry, name_for_debug=name_for_debug)
        tick_signals = self.tick_detection.detect_ticks(rotated_ruler=rotated_ruler, name_for_debug=name_for_debug)
        tick_positions = self.tick_positioning.find_tick_positions(detection=tick_signals, name_for_debug=name_for_debug, rotated_ruler_for_debug=rotated_ruler)
        ruler_scale = self.scale_estimation.estimate_ruler_scale(tick_positions=tick_positions, name_for_debug=name_for_debug, rotated_ruler=rotated_ruler)
        return ruler_scale.pixels_per_mm * 10


    def determine_feret_diameter(
        self,
        image: np.ndarray,
        coral_mask: Segment,
        pixel_per_cm: float,
        name_for_debug: str | None = None,
    ) -> float:
        """
        Determine the maximum Feret diameter of a segmented coral.

        The maximum Feret diameter is the greatest distance between
        any two points on the coral boundary.

        Args:
            image:
                Original BGR image. Used only for debug visualization.

            coral_mask:
                Coral segment containing the polygon boundary.

            pixel_per_cm:
                Number of image pixels corresponding to one centimeter.

            name_for_debug:
                If provided, saves a debug image showing the polygon,
                convex hull, and maximum Feret diameter.

        Returns:
            Maximum Feret diameter in centimeters.
        """

        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                "Image must have shape (H, W, 3)."
            )

        if pixel_per_cm <= 0:
            raise ValueError(
                "pixel_per_cm must be greater than zero."
            )

        if len(coral_mask.polygon) < 2:
            raise ValueError(
                "Coral polygon must contain at least two points."
            )

        polygon = np.asarray(
            [
                (point.x, point.y)
                for point in coral_mask.polygon
            ],
            dtype=np.float32,
        )

        # ---------------------------------------------------------
        # Find convex hull.
        # ---------------------------------------------------------
        #
        # The maximum distance between any two points of a polygon
        # must occur between two points on its convex hull.
        #

        hull_points, point_a, point_b, feret_diameter_pixels = self.vision_service.find_feret_diameter(polygon)

        feret_diameter_cm = feret_diameter_pixels / pixel_per_cm

        # ---------------------------------------------------------
        # Debug image.
        # ---------------------------------------------------------

        if name_for_debug is not None:
            self._save_feret_debug_image(
                image=image,
                polygon=polygon,
                hull=hull_points,
                point_a=point_a,
                point_b=point_b,
                feret_diameter_pixels=(
                    feret_diameter_pixels
                ),
                feret_diameter_cm=(
                    feret_diameter_cm
                ),
                name=name_for_debug,
            )

        return feret_diameter_cm
    
    def _save_feret_debug_image(
        self,
        image: np.ndarray,
        polygon: np.ndarray,
        hull: np.ndarray,
        point_a: np.ndarray,
        point_b: np.ndarray,
        feret_diameter_pixels: float,
        feret_diameter_cm: float,
        name: str,
    ) -> None:
        """
        Save a debug image showing:

            - original coral polygon
            - convex hull
            - maximum Feret diameter
            - measurement
        """

        debug_image = image.copy()

        # ---------------------------------------------------------
        # Draw original segmentation polygon.
        # ---------------------------------------------------------

        polygon_int = np.round(
            polygon
        ).astype(np.int32)

        cv2.polylines(
            debug_image,
            [polygon_int],
            isClosed=True,
            color=(0, 255, 0),
            thickness=2,
            lineType=cv2.LINE_AA,
        )

        # ---------------------------------------------------------
        # Draw convex hull.
        # ---------------------------------------------------------

        hull_int = np.round(
            hull
        ).astype(np.int32)

        cv2.polylines(
            debug_image,
            [hull_int],
            isClosed=True,
            color=(255, 0, 0),
            thickness=2,
            lineType=cv2.LINE_AA,
        )

        # ---------------------------------------------------------
        # Draw Feret diameter.
        # ---------------------------------------------------------

        a = (
            int(round(point_a[0])),
            int(round(point_a[1])),
        )

        b = (
            int(round(point_b[0])),
            int(round(point_b[1])),
        )

        cv2.line(
            debug_image,
            a,
            b,
            (0, 0, 255),
            3,
            cv2.LINE_AA,
        )

        cv2.circle(
            debug_image,
            a,
            6,
            (0, 0, 255),
            -1,
        )

        cv2.circle(
            debug_image,
            b,
            6,
            (0, 0, 255),
            -1,
        )

        # ---------------------------------------------------------
        # Measurement text.
        # ---------------------------------------------------------

        text = (
            f"Feret diameter: "
            f"{feret_diameter_cm:.2f} cm "
            f"({feret_diameter_pixels:.1f} px)"
        )

        cv2.putText(
            debug_image,
            text,
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )

        cv2.putText(
            debug_image,
            text,
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        output_path = (
            Path("test/analysis/measurement/debug")
            / f"{name}_stage_6_feret.png"
        )
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not cv2.imwrite(str(output_path), debug_image):
            raise IOError(
                f"Failed to write ruler detection debug image: {output_path}"
            )