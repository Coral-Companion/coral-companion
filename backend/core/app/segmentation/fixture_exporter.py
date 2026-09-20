from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
import cv2
from datetime import datetime
import numpy as np
from app.persistence.storage import save_debug_image
from .models import Segment

def export_segmentation_fixture(image: np.ndarray, image_filename: str, masks: list[Segment]) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    output_dir = base_dir / "dev_fixtures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    match = re.search(r"(?:CR_)?([A-Za-z0-9]+)(?:_T\d+)?_([A-Za-z0-9]+)(_[A-Za-z0-9]+)?\.(?:jpe?g|png|bmp|tif|tiff|JPE?G|PNG|BMP|TIFF?)", image_filename, re.I)
    site = match.group(1).lower() if match else "default"
    coral_id = f"{match.group(2)}" if match else "default"
    
    fixture_coral_id = f"{site}_{coral_id}"
    
    coral_directory = output_dir / fixture_coral_id
    coral_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M");
    
    target_image_path = coral_directory / f"{timestamp}.jpg"
    target_json_path = coral_directory / f"{timestamp}.json"

    save_debug_image(image, str(target_image_path))

    segments: list[dict[str, Any]] = []
    for segment in masks:
        segments.append(segment_to_fixture(segment))

    height, width = image.shape[:2]
    payload = {
        "coralId": coral_id,
        "coralName": coral_id,
        "image": {
            "width": width,
            "height": height,
        },
        "segments": segments,
    }

    target_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def segment_to_fixture(segment: Segment):
    return {
            "id": segment.id,
            "polygon": segment.polygon,
            "bbox": {
                "x": int(segment.bbox.x),
                "y": int(segment.bbox.y),
                "width": int(segment.bbox.width),
                "height": int(segment.bbox.height),
            },
            "predictedIoU": float(segment.predictedIoU),
            "stabilityScore": float(segment.stabilityScore),
        }
