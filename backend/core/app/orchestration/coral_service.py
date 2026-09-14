from __future__ import annotations

import uuid
from app.orchestration.models import IdentifyResult
import numpy as np
import os
from sqlalchemy.dialects.postgresql import JSONB
from dataclasses import asdict
import logging

from app.cropping.cropper import BoundingBoxCropper
from app.embedding.embedding import EmbeddingService
from app.segmentation.models import SegmentationResult
from app.segmentation.provider_factory import get_segmentation_provider
from app.domain.observation import Observation
from app.orchestration.models import ConfirmResult
from app.persistence.observation_repository import ObservationRepository
from app.domain.models import Segment, ObservationCandidate
from app.persistence.storage import upload_image_to_bucket
from app.vision.vision_service import VisionService
from app.utils.performance_profiler import log_memory, performance_stage


class CoralService:
    """
    Business logic for coral segmentation and identification.
    """
    
    EMBEDDING_VECTOR_DISTANCE_THRESHOLD = float(os.environ.get("EMBEDDING_VECTOR_DISTANCE_THRESHOLD", "0.2"))

    

    def __init__(self) -> None:
        self.segmenter = get_segmentation_provider()
        self.cropper = BoundingBoxCropper()
        self.embedding_service = EmbeddingService()
        self.vision_service = VisionService()
        self.observation_repository = ObservationRepository()
        self.logger = logging.getLogger(__name__)

    def segment_image(self, image: np.ndarray, filename: str) -> SegmentationResult :
        """
        Runs CoralSCOP (or fixture provider) to find coral segment(s) in the given picture.

        Returns SegmentationResult.
        """
        
        with performance_stage("Full Segmentation"):
            result = self.segmenter.segment(image, filename)

        return result

    def find_similar_observations(self, image: np.ndarray, segments: list[Segment]) -> list[ObservationCandidate]:
        """
        Finds similar observations by first calculating the embedding and then comparing it against
        what is stored in the db.
        """

        identify_result = self.identify(image, segments)

        candidates = self.observation_repository.find_similar(identify_result.embedding)

        return self.apply_embedding_distance_filter(candidates)

    def apply_embedding_distance_filter(self, candidates):
        """
        Filter the given candidates according to configured threshold. 
        Can be controlled by environment variable EMBEDDING_VECTOR_DISTANCE_THRESHOLD with values [0..1]
        """
        
        return [candidate for candidate in candidates if candidate.distance < self.EMBEDDING_VECTOR_DISTANCE_THRESHOLD]

    def identify(self, image: np.ndarray, segments: list[Segment]) -> IdentifyResult:
        """
        Creates one merged crop from the selected segments, masks the crop and
        generates an embedding.
        """
        if not segments:
            raise ValueError("No segments selected.")

        mask_result = self.vision_service.mask(image=image, segments=segments)
        crop_result = self.cropper.crop(image=mask_result.masked_image, segments=segments)
        original_embedding = self.embedding_service.generate_vector_embedding(crop_result.crop)

        return IdentifyResult(
            crop=crop_result.crop,
            masked_image=mask_result.masked_image,
            embedding=original_embedding,
            selected_segments=segments,
        )
        
    def prepare_segments_for_db(self, segments: list[Segment]) -> JSONB:
        return [
            asdict(segment)
            for segment in segments
        ]

    def confirm_observation(self, 
            image: np.ndarray,
            segments: list[Segment],
            dive_site: str,
            coral_name: str,
            monitoring_session_id: str
        ) -> ConfirmResult:
        
        identifyResult = self.identify(image, segments)

        observation = Observation()
        observation.coral_name = coral_name
        observation.dive_site = dive_site
        observation.embedding = identifyResult.embedding

        directory_in_bucket = f"{dive_site}/{coral_name}"
        image_path = upload_image_to_bucket(image, f"{directory_in_bucket}/{observation.created_at}")
        observation.image_filename = str(observation.created_at)
        height, width = image.shape[:2]
        observation.image_height = height
        observation.image_width = width
        observation.image_path = image_path
        
        observation.cropped_image_path = upload_image_to_bucket(
            identifyResult.crop, f"{directory_in_bucket}/cropped_{observation.created_at}"
        )
        
        upload_image_to_bucket(
            identifyResult.masked_image, f"{directory_in_bucket}/masked_{observation.created_at}"
        )

        observation.monitoring_session_id = uuid.UUID(monitoring_session_id)

        observation.segments = self.prepare_segments_for_db(segments)
        
        self.observation_repository.save(observation)

        corrected_image = self.vision_service.apply_underwater_corrections(image)
        upload_image_to_bucket(corrected_image, f"{directory_in_bucket}/color_corrected_{observation.created_at}")
        
        result = ConfirmResult(observation)
        return result

    