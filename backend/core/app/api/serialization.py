from app.domain.models import BoundingBox, Point, Segment
from app.orchestration.models import IdentifyResult
from flask import Request
import json
from uuid import UUID

from app.persistence.storage import decode_image_stream
from app.segmentation.models import SegmentationResult
from app.orchestration.models import IdentifyRequest, ConfirmRequest
from app.domain.observation import Observation
from app.domain.monitoring_session import MonitoringSession
from app.domain.models import ObservationCandidate


def serialize_image_upload_response(result: SegmentationResult, observation_candidates: list[ObservationCandidate]) -> dict:
    """
    Convert a SegmentationResult into a JSON-compatible API response.
    """

    return {
        "image": {
            "height": result.image_height,
            "width": result.image_width,
        },
        "segments": [
            {
                "id": segment.id,
                "bbox": {
                    "x": segment.bbox.x,
                    "y": segment.bbox.y,
                    "width": segment.bbox.width,
                    "height": segment.bbox.height,
                },
                "polygon": [
                    [point.x, point.y]
                    for point in segment.polygon
                ],
                "predictedIoU": segment.predictedIoU,
                "stabilityScore": segment.stabilityScore,
            }
            for segment in result.segments
        ],
        "observationCandidates": [
            {
                "id": candidate.observation.id,
                "coralId": candidate.observation.id,
                "coralName": candidate.observation.coral_name,
                "monitoringSessionDate": candidate.observation.monitoring_session.timestamp,
                "visualSimilarity": candidate.similarity,
                "diveSite": candidate.observation.dive_site,
                # intentionally return a smaller image
                "imageUrl": candidate.observation.cropped_image_path,
            }
            for candidate in observation_candidates
        ]
    }
    
def _extract_file_from_request(request: Request, parameter_name: str):
    uploaded_file = request.files[parameter_name]
    if uploaded_file is None:
        raise ValueError("[API] Missing image.")
    return uploaded_file

def parse_identify_request(request) -> IdentifyRequest:
    """
    Convert the http request into a IdentifyRequest for processing
    """
    uploaded_file = _extract_file_from_request(request, "image")
    image = decode_image_stream(uploaded_file)
    segments_form_field = request.form["segments"]
    segments_form_payload = json.loads(segments_form_field)
    segments_payload_field_key = "selectedSegments"
    segments_json_array = segments_form_payload[segments_payload_field_key]
    segments = parse_segments(segments_json_array)

    return IdentifyRequest(image=image, selected_segments=segments)
    
def serialize_observation_candidates(observations: list[ObservationCandidate]) -> dict:
    return {
        "candidates": [
            {
                "id": candidate.observation.id,
                "coralId": candidate.observation.id,
                "coralName": candidate.observation.coral_name,
                "monitoringSessionDate": candidate.observation.monitoring_session.timestamp,
                "visualSimilarity": candidate.similarity,
                "diveSite": candidate.observation.dive_site,
                # intentionally return a smaller, cropped image
                "imageUrl": candidate.observation.cropped_image_path,
            }
            for candidate in observations
        ]
    }
    
def parse_confirm_request(request: Request) -> ConfirmRequest:
    """
    Convert the http request into a ConfirmRequest for processing
    """
    uploaded_file = _extract_file_from_request(request, "image")
    image = decode_image_stream(uploaded_file)

    segments_form_field = request.form["segments"]
    segments_form_payload = json.loads(segments_form_field)
    segments_payload_field_key = "selectedSegments"
    segments_json_array = segments_form_payload[segments_payload_field_key]
    segments = parse_segments(segments_json_array)

    dive_site = request.form["diveSite"]
    coral_name = request.form["coralName"]
    monitoring_session_id = request.form["monitoringSessionId"]
    
    return ConfirmRequest(image, segments, dive_site, coral_name, monitoring_session_id)

def parse_segments(segments_json_array):
    return [
        Segment(
            id=segment["id"],
            bbox=BoundingBox(
                x=segment["bbox"]["x"],
                y=segment["bbox"]["y"],
                width=segment["bbox"]["width"],
                height=segment["bbox"]["height"],
            ),
            polygon=[
                Point(
                    x=point[0],
                    y=point[1],
                )
                for point in segment["polygon"]
            ],
            predictedIoU=segment["predictedIoU"],
            stabilityScore=segment["stabilityScore"],
        )
        for segment in segments_json_array
    ]
    
def parse_monitoring_session(request: Request) -> MonitoringSession:
    body = request.json
    monitoring_session = MonitoringSession(name=body["name"], timestamp=body["timestamp"], dive_site=body["diveSite"])
    return monitoring_session

def serialize_monitoring_sessions(sessions: list[MonitoringSession]):
    return {
        "sessions": [
            {
                "id": session.id,
                "diveSite": session.dive_site,
                "name": session.name,
                "timestamp": session.timestamp,
            }
            for session in sessions
        ]
    }
    
def parse_observation_comparison_ids(request: Request) -> list[UUID]:
    body = request.json
    return [UUID(id) for id in body["observationIds"]]