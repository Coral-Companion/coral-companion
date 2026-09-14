import logging
import sys
import functions_framework
from flask import Request
import numpy as np
from functools import reduce
import re
from uuid import UUID

from app.orchestration.coral_service import CoralService
from app.orchestration.comparison_service import ComparisonService
from app.persistence.storage import decode_image_stream
from app.persistence.monitoring_session_repository import MonitoringSessionRepository
from app.persistence.observation_repository import ObservationRepository
from app.api.serialization import parse_identify_request, serialize_observation_candidates, serialize_image_upload_response, parse_confirm_request, parse_monitoring_session, serialize_monitoring_sessions, parse_observation_comparison_ids
from app.api.models import MonitoringSessionResponse, ObservationSummary
from app.domain.monitoring_session import MonitoringSession
from app.orchestration.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )

coral_service = CoralService()
comparison_service = ComparisonService()
monitoring_session_repository = MonitoringSessionRepository()
observation_repository = ObservationRepository()
analysis_service = AnalysisService()

def add_cors_headers(body, status=200):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    return body, status, headers

def extract_file_from_request(request: Request, parameter_name: str):
    uploaded_file = request.files.get(parameter_name)
    if uploaded_file is None:
        raise ValueError("[API] Missing image.")
    return uploaded_file

@functions_framework.http
def process_coral_upload(request: Request):
    logger.info("%s %s", request.method, request.path)

    if request.method == "OPTIONS":
        return add_cors_headers("", 204)

    try:
        if request.path == "/api/upload-coral-image":
            uploaded_file = extract_file_from_request(request, "image")
            image: np.ndarray = decode_image_stream(uploaded_file)
            segmentation = coral_service.segment_image(
                image=image,
                filename=uploaded_file.filename or "uploaded.jpg"
            )
            
            candidates = []
            if (len(segmentation.segments) > 0):
                segment = reduce(
                    lambda segment, other: segment if segment.score() > other.score() else other,
                    segmentation.segments
                )
                candidates = coral_service.find_similar_observations(image, [segment])
                response = serialize_image_upload_response(segmentation, candidates)
            else:
                logger.warning(f"Segments are empty {segmentation} for {uploaded_file.filename}")
            return add_cors_headers(serialize_image_upload_response(segmentation, candidates))

        if request.path == "/api/identify-by-segments":
            identify_request = parse_identify_request(request)
            observationCandidates = coral_service.find_similar_observations(identify_request.image, identify_request.selected_segments)
            
            response = serialize_observation_candidates(observationCandidates)
            return add_cors_headers(response)
        
        if request.path == "/api/confirm-coral":
            confirm_request = parse_confirm_request(request)
            observation = coral_service.confirm_observation(
                confirm_request.image,
                confirm_request.selected_segments,
                confirm_request.dive_site,
                confirm_request.coral_name,
                confirm_request.monitoring_session_id
            ).observation
            return add_cors_headers({"observationId": observation.id})

        if request.path == "/api/monitoring-sessions" and request.method == "POST":
            monitoring_session: MonitoringSession = parse_monitoring_session(request)
            monitoring_session = monitoring_session_repository.save(monitoring_session)
            return add_cors_headers({"monitoringSessionId": monitoring_session.id})

        if request.path == "/api/monitoring-sessions" and request.method == "GET":
            sessions = monitoring_session_repository.find_all()
            monitoring_observation_counts = observation_repository.find_amount_per_session()
            response = [
                MonitoringSessionResponse(
                    id=session.id,
                    name=session.name,
                    timestamp=session.timestamp,
                    dive_site=session.dive_site,
                    observation_count=monitoring_observation_counts.get(str(session.id), 0),
                ).model_dump(by_alias=True)
                for session in sessions
            ]
            return add_cors_headers(response)
        
        if request.path == "/api/observation-summaries" and request.method == "GET":
            summaries = observation_repository.find_all_summaries()
            response = [
                summary.model_dump(by_alias=True)
                for summary in summaries
            ]
            return add_cors_headers(response)
        
        if request.path == "/api/observations/comparisons" and request.method == "POST":
            ids = parse_observation_comparison_ids(request)
            response = [
                comparison.model_dump(by_alias=True)
                for comparison in comparison_service.compare_observations(ids)
                ]
            return add_cors_headers(response);
        
        pattern = r"^/api/observations/([^/]+)/metrics/visualizations/?$"
        match = re.match(pattern, request.path)
        if match and request.method == "GET":
            observation_id = UUID(match.group(1))
            visualizations = analysis_service.analyse_visually(observation_id)
            return add_cors_headers(visualizations);
        
        return add_cors_headers({"error": "Unknown endpoint."}, 404)

    except ValueError as ex:
        logger.exception(f"[API] An error has occurred: {str(ex)}", ex)
        return add_cors_headers({"error": str(ex)}, 400)

    except Exception as ex:
        logger.exception(ex)
        return add_cors_headers({"error": "Internal server error."}, 500)
