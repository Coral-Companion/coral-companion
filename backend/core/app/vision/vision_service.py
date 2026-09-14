import numpy as np
import cv2

from app.domain.models import Segment
from app.vision.models import MaskResult

class VisionService:
    """
    Provides vision-related functions
    """
    
    def mask(self, image: np.ndarray, segments: list[Segment]) -> MaskResult:
        """
        Masks the image with the given segments. The rest of the picture will be transparent. The 
        masked_image in the result is going to be rgba
        """
        alpha = np.zeros(image.shape[:2], dtype=np.uint8)

        polygons = [
            np.array(
                [(point.x, point.y) for point in segment.polygon],
                dtype=np.int32,
            )
            for segment in segments
        ]

        cv2.fillPoly(alpha, polygons, 255)

        rgba = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
        
        # set alpha channel to zero for area outside mask
        rgba[:, :, 3] = alpha
        
        # still make area outside mask black just in case
        rgba[alpha == 0, :3] = 0

        return MaskResult(masked_image=rgba)


    def rotate_image(self, image, angle):
        """
        Rotate an OpenCV image by 0, 90, 180, or 270 degrees.
        """

        if angle == 0:
            return image.copy()

        if angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

        if angle == 180:
            return cv2.rotate(image, cv2.ROTATE_180)

        if angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        raise ValueError(f"Unsupported rotation angle: {angle}")


    def apply_underwater_corrections(self, image: np.ndarray) -> np.ndarray:
        """
        Applies underwater enhancement to an RGB or RGBA image.

        Returns an image with the same number of channels as the input.
        """

        if image is None or image.size == 0:
            raise ValueError("Empty image matrix passed to processing engine.")

        # Preserve alpha channel if present
        if image.shape[2] == 4:
            alpha = image[:, :, 3].copy()
            rgb = image[:, :, :3]
        else:
            alpha = None
            rgb = image

        # ------------------------------------------------------------------
        # 1. CLAHE Contrast Equalization
        # ------------------------------------------------------------------

        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)

        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(
            clipLimit=3.0,
            tileGridSize=(8, 8),
        )

        l_channel = clahe.apply(l_channel)

        enhanced_lab = cv2.merge((l_channel, a_channel, b_channel))

        rgb_enhanced = cv2.cvtColor(
            enhanced_lab,
            cv2.COLOR_LAB2RGB,
        )

        # ------------------------------------------------------------------
        # 2. Gray World White Balance
        # ------------------------------------------------------------------

        r, g, b = cv2.split(rgb_enhanced)

        mean_r = np.mean(r)
        mean_g = np.mean(g)
        mean_b = np.mean(b)

        mean_gray = (mean_r + mean_g + mean_b) / 3.0

        scale_r = mean_gray / mean_r if mean_r > 0 else 1.0
        scale_g = mean_gray / mean_g if mean_g > 0 else 1.0
        scale_b = mean_gray / mean_b if mean_b > 0 else 1.0

        r = np.clip(r * scale_r, 0, 255).astype(np.uint8)
        g = np.clip(g * scale_g, 0, 255).astype(np.uint8)
        b = np.clip(b * scale_b, 0, 255).astype(np.uint8)

        rgb_balanced = cv2.merge((r, g, b))

        # ------------------------------------------------------------------
        # Restore alpha if present
        # ------------------------------------------------------------------

        if alpha is not None:
            rgba = cv2.cvtColor(rgb_balanced, cv2.COLOR_RGB2RGBA)
            rgba[:, :, 3] = alpha
            return rgba

        return rgb_balanced

    def draw_mask(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        alpha: float = 0.7,
    ) -> np.ndarray:
        """
        Overlay a binary mask in red onto an image.

        Args:
            image: Grayscale or BGR image.
            mask: Binary mask with shape (H, W).
            alpha: Opacity of the red overlay.

        Returns:
            BGR image with masked pixels highlighted in red.
        """

        if image.ndim == 2:
            result = cv2.cvtColor(
                image,
                cv2.COLOR_GRAY2BGR,
            )
        elif image.ndim == 3 and image.shape[2] == 3:
            result = image.copy()
        else:
            raise ValueError(
                "Image must have shape (H, W) or (H, W, 3)."
            )

        if mask.shape != image.shape[:2]:
            raise ValueError(
                "Mask dimensions must match image dimensions."
            )

        if not 0.0 <= alpha <= 1.0:
            raise ValueError(
                "Alpha must be between 0 and 1."
            )

        mask_bool = mask > 0

        red = np.zeros_like(result)
        red[:, :] = (0, 0, 255)  # BGR

        result[mask_bool] = cv2.addWeighted(
            result[mask_bool],
            1.0 - alpha,
            red[mask_bool],
            alpha,
            0,
        )

        return result


    def find_feret_diameter(self, polygon: np.ndarray):
        hull = cv2.convexHull(
            polygon
        )

        hull_points = (
            hull[:, 0, :]
            .astype(np.float64)
        )

        if len(hull_points) < 2:
            raise ValueError(
                "Coral polygon has an invalid convex hull."
            )

        # ---------------------------------------------------------
        # Find the two hull points with the greatest distance.
        # ---------------------------------------------------------

        differences = (
            hull_points[:, np.newaxis, :]
            - hull_points[np.newaxis, :, :]
        )

        squared_distances = np.sum(
            differences ** 2,
            axis=2,
        )

        point_indices = np.unravel_index(
            np.argmax(
                squared_distances
            ),
            squared_distances.shape,
        )

        point_a = hull_points[
            point_indices[0]
        ]

        point_b = hull_points[
            point_indices[1]
        ]

        feret_diameter_pixels = float(
            np.sqrt(
                squared_distances[
                    point_indices
                ]
            )
        )
        return hull_points, point_a, point_b, feret_diameter_pixels