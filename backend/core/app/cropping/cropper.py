from __future__ import annotations

import os
import numpy as np
import cv2

from app.domain.models import Segment, BoundingBox
from .models import CropResult

CROPPING_PADDING_RATIO = float(os.environ.get("CROPPING_PADDING_RATIO", "0.15"))

class BoundingBoxCropper:

   
    def crop(self, image: np.ndarray, segments: list[Segment], padding_ratio: float = 0.15) -> CropResult:
        """
        Creates a padded square crop around one or multiple selected segments.
        """
        
        if image is None or image.size == 0:
            raise ValueError("Image is empty.")

        if not segments:
            raise ValueError("No segments supplied.")

        content_box = self._compute_content_box(segments)
        padding = int(max(content_box.width, content_box.height) * padding_ratio)
        padded_box = self._expand_with_padding(content_box, padding)
        
        square_box = self._make_square(padded_box)

        # required so that a square can be made out of a very large rectangular box
        padded_image, adjusted_box = self._pad_image_for_crop(image, square_box)
                
        if not self._contains(square_box, content_box):
            raise ValueError(
                f"Final crop box {square_box} does not contain "
                f"content box {content_box} "
                f"for image with {len(segments)} segments"
            )
        
        crop = self._crop_image(padded_image, adjusted_box)

        return CropResult(
            crop=crop,
            content_box=content_box,
            square_box=square_box,
            padding=padding,
        )

    def _compute_content_box(self, segments: list[Segment]) -> BoundingBox:
        first = segments[0].bbox
        min_x = first.x
        min_y = first.y
        max_x = first.x + first.width
        max_y = first.y + first.height

        for segment in segments[1:]:

            if segment.bbox is None:
                raise ValueError("Segment has no bounding box.")

            x = segment.bbox.x
            y = segment.bbox.y
            width = segment.bbox.width
            height = segment.bbox.height

            min_x = min(min_x, x)
            min_y = min(min_y, y)

            max_x = max(max_x, x + width)
            max_y = max(max_y, y + height)

        return BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y,
        )

    def _expand_with_padding(self, box: BoundingBox, padding: int) -> BoundingBox:

        return BoundingBox(
            x=box.x - padding,
            y=box.y - padding,
            width=box.width + padding * 2,
            height=box.height + padding * 2,
        )

    def _make_square(self, box: BoundingBox) -> BoundingBox:
        side = max(box.width, box.height)
        cx, cy = box.center

        x = int(round(cx - side / 2))
        y = int(round(cy - side / 2))

        return BoundingBox(
            x=x,
            y=y,
            width=side,
            height=side,
        )
        
    def _pad_image_for_crop(
        self,
        image: np.ndarray,
        crop_box: BoundingBox,
    ) -> tuple[np.ndarray, BoundingBox]:
        """
        Pads the image with black pixels whenever the desired crop
        extends beyond the original image boundaries.
        """

        image_height, image_width = image.shape[:2]

        left_padding = max(0, -crop_box.x)
        top_padding = max(0, -crop_box.y)

        right_padding = max(0, crop_box.x2 - image_width)

        bottom_padding = max(0, crop_box.y2 - image_height)

        if any(
            padding > 0
            for padding in (
                left_padding,
                top_padding,
                right_padding,
                bottom_padding,
            )
        ):
            padded_image = cv2.copyMakeBorder(
                image,
                top=top_padding,
                bottom=bottom_padding,
                left=left_padding,
                right=right_padding,
                borderType=cv2.BORDER_CONSTANT,
                value=(0, 0, 0),
            )
        else:
            padded_image = image

        adjusted_box = BoundingBox(
            x=crop_box.x + left_padding,
            y=crop_box.y + top_padding,
            width=crop_box.width,
            height=crop_box.height,
        )

        return padded_image, adjusted_box

    def _clip_to_image(
        self, box: BoundingBox, image_shape: tuple[int, ...]) -> BoundingBox:
        
        image_height, image_width = image_shape[:2]
        x = box.x
        y = box.y
        side = box.width

        # Shift square back into image instead of shrinking it.

        if x < 0:
            x = 0

        if y < 0:
            y = 0

        if x + side > image_width:
            x = image_width - side

        if y + side > image_height:
            y = image_height - side

        # If the coral is larger than the image,
        # fall back to the whole image.

        x = max(0, x)
        y = max(0, y)

        side = min(
            side,
            image_width,
            image_height,
        )

        return BoundingBox(
            x=x,
            y=y,
            width=side,
            height=side,
        )

    def _contains(self, outer: BoundingBox, inner: BoundingBox) -> bool:
        return (
            outer.x <= inner.x
            and outer.y <= inner.y
            and outer.x2 >= inner.x2
            and outer.y2 >= inner.y2
        )

    def _crop_image(self, image: np.ndarray, box: BoundingBox) -> np.ndarray:
        return image[box.y:box.y2, box.x:box.x2].copy()