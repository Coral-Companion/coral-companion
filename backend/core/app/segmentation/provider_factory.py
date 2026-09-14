from __future__ import annotations

import logging
import os

from app.segmentation.fixture_provider import FixtureProvider
from app.segmentation.segmentation_provider import SegmentationProvider
from app.segmentation.coralscop_provider import CoralScopProvider

logger = logging.getLogger(__name__)


def get_segmentation_provider() -> SegmentationProvider:
    provider_name = os.environ.get("SEGMENTATION_PROVIDER", "coralscop").strip().lower()
    if provider_name == "coralscop":
        try:
            return CoralScopProvider()
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("[Segmentation] CoralSCOP provider failed to initialize, falling back to fixture provider: %s", exc)
            return FixtureProvider()
    elif provider_name == "fixture":
        return FixtureProvider()
    raise ValueError(f"Unsupported segmentation provider: {provider_name}")
