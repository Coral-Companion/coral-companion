import logging
import sys
from functools import reduce
from typing import List
from uuid import UUID

from fastapi import FastAPI, UploadFile, File, Form, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from dotenv import load_dotenv
load_dotenv()

from app.orchestration.coral_service import CoralService
from app.orchestration.comparison_service import ComparisonService
from app.persistence.storage import decode_image_bytes
from app.persistence.monitoring_session_repository import MonitoringSessionRepository
from app.persistence.observation_repository import ObservationRepository
from app.orchestration.analysis_service import AnalysisService

from app.api.schemas import (
    ImageUploadResponse,
    IdentifyResponse,
    ConfirmCoralResponse,
    CreateMonitoringSessionResponse,
    MonitoringSessionCreate,
    ObservationComparisonRequest,
    ObservationCandidateResponse,
    parse_segments_form_data
)
from app.api.models import MonitoringSessionResponse, ObservationSummary

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)
logger = logging.getLogger("uvicorn.error")

coral_service = CoralService()
comparison_service = ComparisonService()
monitoring_session_repository = MonitoringSessionRepository()
observation_repository = ObservationRepository()
analysis_service = AnalysisService()

app = FastAPI(title="Coral Companion core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.exception(f"[API] Validation Error: {exc}")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"[API] Unhandled server error: {exc}")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Internal server error."})

@app.post("/api/upload-coral-image", response_model=ImageUploadResponse)
async def upload_coral_image(image: UploadFile = File(...)):
    image_bytes = await image.read()
    img_array: np.ndarray = decode_image_bytes(image_bytes)
    segmentation = await coral_service.segment_image(
        image=image_bytes,
        filename=image.filename or "uploaded.jpg"
    )
    
    candidates = []
    if len(segmentation.segments) > 0:
        best_segment = reduce(
            lambda s, other: s if s.score() > other.score() else other,
            segmentation.segments
        )
        candidates = coral_service.find_similar_observations(img_array, [best_segment])
    else:
        logger.warning(f"Segments are empty for {image.filename}")
        
    return ImageUploadResponse.from_domain(segmentation, candidates)


@app.post("/api/identify-by-segments", response_model=IdentifyResponse)
async def identify_by_segments(
    image: UploadFile = File(...),
    segments: str = Form(..., description="JSON stringified segments payload")
):
    image_bytes = await image.read()
    img_array = decode_image_bytes(image_bytes)
    parsed_segments = parse_segments_form_data(segments)
    
    observation_candidates = coral_service.find_similar_observations(img_array, parsed_segments)
    
    return IdentifyResponse(
        candidates=[ObservationCandidateResponse.from_domain(c) for c in observation_candidates]
    )


@app.post("/api/confirm-coral", response_model=ConfirmCoralResponse)
async def confirm_coral(
    image: UploadFile = File(...),
    segments: str = Form(...),
    diveSite: str = Form(...),
    coralName: str = Form(...),
    monitoringSessionId: UUID = Form(...)
):
    image_bytes = await image.read()
    img_array = decode_image_bytes(image_bytes)
    parsed_segments = parse_segments_form_data(segments)

    observation = coral_service.confirm_observation(
        img_array,
        parsed_segments,
        diveSite,
        coralName,
        str(monitoringSessionId)
    ).observation
    
    return ConfirmCoralResponse(observationId=observation.id)


@app.post("/api/monitoring-sessions", response_model=CreateMonitoringSessionResponse)
async def create_monitoring_session(payload: MonitoringSessionCreate):
    session = monitoring_session_repository.save(payload.to_domain())
    return CreateMonitoringSessionResponse(monitoringSessionId=session.id)


@app.get("/api/monitoring-sessions", response_model=List[MonitoringSessionResponse])
async def get_monitoring_sessions():
    sessions = monitoring_session_repository.find_all()
    observation_counts = observation_repository.find_amount_per_session()
    
    return [
        MonitoringSessionResponse(
            id=session.id,
            name=session.name,
            timestamp=session.timestamp,
            dive_site=session.dive_site,
            observation_count=observation_counts.get(str(session.id), 0),
        )
        for session in sessions
    ]


@app.get("/api/observation-summaries", response_model=List[ObservationSummary])
async def get_observation_summaries():
    # If ObservationSummary is already a Pydantic model (based on your snippet `model_dump()`),
    # FastAPI will serialize it automatically.
    return observation_repository.find_all_summaries()


@app.post("/api/observations/comparisons")
async def compare_observations(payload: ObservationComparisonRequest):
    comparisons = comparison_service.compare_observations(payload.observationIds)
    # Returning raw models, FastAPI will call `model_dump()` natively underneath
    return comparisons


@app.get("/api/observations/{observation_id}/metrics/visualizations")
async def get_visualizations(observation_id: UUID):
    # The Path parameter is automatically extracted and cast to a UUID.
    visualizations = analysis_service.analyse_visually(observation_id)
    return visualizations
