from __future__ import annotations

import numpy as np

from app.segmentation.models import SegmentationResult
from app.segmentation.segmentation_provider import SegmentationProvider
from app.segmentation.fixture_exporter import export_segmentation_fixture

import os
import logging
import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError
from typing import BinaryIO
import json

SEGMENTATION_WORKER_URL = os.getenv("SEGMENTATION_WORKER_URL", "http://localhost:8001")
PRODUCE_FIXTURES = os.getenv("PRODUCE_FIXTURES", False)

class CoralScopProvider(SegmentationProvider):
    """Calls segmentation service."""
    
    def __init__(self, base_url: str = SEGMENTATION_WORKER_URL):
        self.base_url = base_url.rstrip("/")
        self.logger = logging.getLogger("uvicorn.error")
    
    async def segment(self, image: bytes, image_filename: str) -> SegmentationResult:
        """
        Sends raw image bytes as multipart/form-data to the segmentation worker
        and returns the parsed SegmentationResult schema.
        """
        url = f"{self.base_url}/api/segment"
        files = {"file": (image_filename, image, "image/jpeg")}
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, files=files)
                response.raise_for_status()
                response_json = response.json()
                # 1. Print exactly what the worker sent
                print("🚨 RAW JSON FROM WORKER:")
                print(json.dumps(response_json, indent=2))
                
                # 2. Try to validate
                result = SegmentationResult.model_validate(response_json["result"])

            except ValidationError as e:
                # 3. Print exactly why Pydantic rejected it
                print("🚨 PYDANTIC VALIDATION ERROR:")
                print(e)
                raise  # Re-raise so your app still fails properly during debugging

            except httpx.ConnectError:
                self.logger.error(f"Could not connect to ML Worker at {self.base_url}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Segmentation worker service is currently unreachable.",
                )
                
            except httpx.HTTPStatusError as e:
                self.logger.error(f"ML Worker returned error: {e.response.text}")
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Segmentation worker failed: {e.response.text}",
                )
                
            except httpx.RequestError as e:
                self.logger.error(f"Request error calling ML worker: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error communicating with segmentation service.",
                )
        
        if PRODUCE_FIXTURES:
            try:
                export_segmentation_fixture(image, image_filename, result.segments)
            except Exception as e:
                self.logger.exception(f"[Segmentation] Failed writing fixture. {str(e)}")
        
        return result

