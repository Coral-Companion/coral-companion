from .models import RotatedRuler, RulerGeometry
import numpy as np
import cv2
from pathlib import Path

class RulerRotation:
    """
    Rotates a given ruler horizontally for further 1 dimensional processing
    <br />
    <br />
    Produces a debug image with a horizontal ruler axis
    """
    
    def rotate_ruler(
        self,
        image: np.ndarray,
        ruler_mask: np.ndarray,
        geometry: RulerGeometry,
        name_for_debug: str | None = None,
    ) -> RotatedRuler:

        self._validate_inputs(
            image=image,
            ruler_mask=ruler_mask,
            geometry=geometry,
        )

        # geometry.angle_degrees describes the LONG AXIS of the ruler.
        #
        # We want that axis to become horizontal (0°).
        #
        # OpenCV uses positive angles for counter-clockwise rotation,
        # therefore rotate by the negative of the ruler angle.
        rotation_angle = geometry.angle_degrees

        center = (
            float(geometry.center[0]),
            float(geometry.center[1]),
        )

        rotation_matrix = cv2.getRotationMatrix2D(
            center=center,
            angle=rotation_angle,
            scale=1.0,
        )

        height, width = image.shape[:2]

        rotated_image = cv2.warpAffine(
            image,
            rotation_matrix,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
        )

        rotated_mask = cv2.warpAffine(
            ruler_mask,
            rotation_matrix,
            (width, height),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
        )

        rotated_mask = np.where(
            rotated_mask > 0,
            255,
            0,
        ).astype(np.uint8)
        
        rotated_contours, _ = cv2.findContours(
            rotated_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if rotated_contours:
            rotated_contour = max(
                rotated_contours,
                key=cv2.contourArea,
            )

            (_, _), (w, h), angle = cv2.minAreaRect(rotated_contour)

            print(
                f"[RULER ROTATION] "
                f"input_angle={geometry.angle_degrees:.2f}° "
                f"rotation={rotation_angle:.2f}° "
                f"rotated_rect=(w={w:.1f}, h={h:.1f}, angle={angle:.2f}°)"
            )

        crop = self._calculate_crop(rotated_mask)

        x, y, crop_width, crop_height = crop

        cropped_image = rotated_image[
            y : y + crop_height,
            x : x + crop_width,
        ]

        cropped_mask = rotated_mask[
            y : y + crop_height,
            x : x + crop_width,
        ]

        result = RotatedRuler(
            image=cropped_image,
            mask=cropped_mask,
            crop=crop,
        )
        
        if name_for_debug:
            self._save_debug_image(
                result=result,
                name=name_for_debug,
            )

        return result

    def _validate_inputs(
        self,
        image: np.ndarray,
        ruler_mask: np.ndarray,
        geometry: RulerGeometry,
    ) -> None:
        if image is None or image.size == 0:
            raise ValueError(
                "Empty image passed to ruler rotation."
            )

        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                "Ruler rotation expects a BGR image with shape (H, W, 3)."
            )

        if ruler_mask is None or ruler_mask.size == 0:
            raise ValueError(
                "Empty ruler mask passed to ruler rotation."
            )

        if ruler_mask.shape != image.shape[:2]:
            raise ValueError(
                "Ruler mask must have the same spatial dimensions as image."
            )

        if not np.any(ruler_mask):
            raise ValueError(
                "Ruler mask contains no detected ruler pixels."
            )

        if geometry.width <= 0 or geometry.height <= 0:
            raise ValueError(
                "Ruler geometry must have positive dimensions."
            )


    def _calculate_crop(
        self,
        rotated_mask: np.ndarray,
    ) -> tuple[int, int, int, int]:
        """
        Calculate a tight bounding box around the rotated ruler mask.
        """
        points = cv2.findNonZero(rotated_mask)

        if points is None:
            raise ValueError(
                "Unable to determine crop: rotated ruler mask is empty."
            )

        x, y, width, height = cv2.boundingRect(points)

        if width <= 0 or height <= 0:
            raise ValueError(
                "Unable to determine a valid ruler crop."
            )

        return x, y, width, height


    def _save_debug_image(
        self,
        result: RotatedRuler,
        name: str | None,
    ) -> None:
        if name is None:
            return

        debug = result.image.copy()

        # Show the detected ruler mask as an outline.
        contours, _ = cv2.findContours(
            result.mask,
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

        output_path = (
            Path("test/analysis/measurement/debug")
            / f"{name}_stage_2_ruler_rotation.png"
        )
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not cv2.imwrite(
            str(output_path),
            debug,
        ):
            raise IOError(
                f"Failed to write ruler rotation debug image: {output_path}"
            )