import pickle
from pathlib import Path
from typing import TypeVar
import json

from app.domain.models import Segment, Point, BoundingBox

T = TypeVar("T")

FIXTURES_DIRECTORY = Path(__file__).parents[2] / "dev_fixtures"


def save_pickle(coral_name: str, name: str, value: object) -> None:
    path = FIXTURES_DIRECTORY / coral_name / f"{name}.pkl"
    with path.open("wb") as f:
        pickle.dump(value, f)


def load_pickle(coral_name: str, name: str) -> T:
    path = FIXTURES_DIRECTORY / coral_name / f"{name}.pkl"
    with path.open("rb") as f:
        return pickle.load(f)


def get_fixture_image_path(coral_name: str, image_name: str | None = None) -> Path:
    file_type = "jpg"
    return get_fixture_file(coral_name, image_name, file_type)


def get_fixture_json_path(coral_name: str, json_filename: str | None = None) -> Path:
    file_type = "json"
    return get_fixture_file(coral_name, json_filename, file_type)


def get_fixture_file(coral_name, file_name, file_type):
    base_dir = Path(__file__).parents[2]
    if file_name is None:
        path = sorted((base_dir / FIXTURES_DIRECTORY / coral_name).glob(f"*.{file_type}"))[0]
    else:
        path = base_dir / FIXTURES_DIRECTORY / coral_name / file_name
    
    return path


def get_segments(coral_name: str, image_filename: str) -> list[Segment]:
        json_file = get_fixture_json_path(coral_name, image_filename)

        with json_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        
        segments_payload = payload.get("segments", [])
        segments: list[Segment] = []

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
            
            return segments