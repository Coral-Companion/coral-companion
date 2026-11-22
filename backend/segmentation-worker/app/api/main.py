import gc
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from third_party.coralscop.segment_anything import (
    SamAutomaticMaskGenerator,
    sam_model_registry,
)
from app.utils.performance_profiler import performance_stage
from .models import BoundingBox, Point, Segment, SegmentationResult


logger = logging.getLogger("uvicorn.error")

MODEL_TYPE = "vit_b"
MAX_UPLOAD_MEGABYTES = 15
MAX_UPLOAD_BYTES = MAX_UPLOAD_MEGABYTES * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000

DEFAULT_LAYERS = 0
DEFAULT_POINTS_PER_SIDE = 10
DEFAULT_POINTS_PER_BATCH = 32


def load_mask_generator_model(checkpoint_path: Path, device: str):
    """Load CoralSCOP mask generator model once and return it."""
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")

    logger.info(f"Loading CoralSCOP: device={device} checkpoint={checkpoint_path}")

    sam = sam_model_registry[MODEL_TYPE](checkpoint=str(checkpoint_path))
    sam.to(device=device)

    logger.info("CoralSCOP loaded successfully on %s", device)
    return sam


def create_mask_generator(model, layers: int, points_per_side: int, points_per_batch: int) -> SamAutomaticMaskGenerator:
    """Create a SamAutomaticMaskGenerator for the given SAM model and crop layers."""
    return SamAutomaticMaskGenerator(
        model=model,
        points_per_side=points_per_side,
        pred_iou_thresh=0.75,
        stability_score_thresh=0.75,
        crop_n_layers=layers,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=100,
        points_per_batch=points_per_batch,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing segmentation worker")

    checkpoint_path = (
        Path(__file__).resolve().parents[2]
        / "third_party"
        / "coralscop"
        / "checkpoints"
        / "vit_b_coralscop.pth"
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"

    app.state.mask_generator_model = None
    app.state.device = device

    try:
        app.state.mask_generator_model = load_mask_generator_model(checkpoint_path, device)
        yield
    finally:
        logger.info("Cleaning up segmentation worker")
        app.state.mask_generator_model = None
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("Segmentation worker cleanup completed")

app = FastAPI(
    title="Coral Segmentation Worker",
    lifespan=lifespan,
)

@app.post("/api/segment")
async def segment_image(
    request: Request,
    file: UploadFile = File(...),
    layers: int = Form(DEFAULT_LAYERS),
    points_per_side: int = Form(DEFAULT_POINTS_PER_SIDE),
    points_per_batch: int = Form(DEFAULT_POINTS_PER_BATCH),
):
    if layers is None or layers < 0 or layers > 5:
        layers = DEFAULT_LAYERS
    if (points_per_side < 0 or points_per_side > 100):
        points_per_side = DEFAULT_POINTS_PER_SIDE
    if (points_per_batch < 0 or points_per_batch > 1_000):
        points_per_batch = DEFAULT_POINTS_PER_BATCH

    sam_model = getattr(request.app.state, "mask_generator_model", None)
    if sam_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")

    try:
        image, rgb = await prepare_image(file)
    finally:
        await file.close()

    try:
        logger.info(
            f"Starting inference: width={image.shape[1]} height={image.shape[0]} device={request.app.state.device} layers={layers} points_per_batch={points_per_batch} points_per_side={points_per_side}"
        )

        mask_generator = create_mask_generator(sam_model, layers, points_per_side, points_per_batch)

#        with performance_stage("Segmentation"):
        masks = mask_generator.generate(rgb)

        segments: list[Segment] = []

        for index, mask_record in enumerate(masks):
            segmentation = mask_record.get("segmentation")
            bbox = mask_record.get("bbox", [0, 0, 0, 0])
            polygon_points = []

            if isinstance(segmentation, np.ndarray):
                mask = segmentation
                mask = (mask > 0).astype(np.uint8) * 255
                contours, _ = cv2.findContours(
                    mask,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_NONE,
                )
                if contours:
                    contour = max(contours, key=cv2.contourArea)
                    polygon_points = [
                        Point(int(x), int(y))
                        for x, y in contour.reshape(-1, 2)
                    ]

            segments.append(
                build_segment(index, mask_record, bbox, polygon_points)
            )

        height, width = image.shape[:2]
        logger.info(f"Inference resulted in {len(segments)} segments")

        result = SegmentationResult(
            image_width=int(width),
            image_height=int(height),
            segments=segments,
        )
        return JSONResponse(
            content={"result": jsonable_encoder(asdict(result))}
        )

    except Exception:
        logger.exception("Segmentation inference failed")
        raise HTTPException(
            status_code=500,
            detail="Segmentation inference failed.",
        )

async def prepare_image(file: UploadFile):
    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Image exceeds the {MAX_UPLOAD_MEGABYTES} MB limit.")

    file_array = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(file_array, cv2.IMREAD_COLOR)

    if image is None:
        logger.warning("Image decoding failed")
        raise HTTPException(status_code=400, detail="Invalid image file format.")

    height, width = image.shape[:2]
    if height * width > MAX_IMAGE_PIXELS:
        raise HTTPException(
            status_code=413,
            detail="Image dimensions exceed the allowed pixel limit.",
        )

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image, rgb


def build_segment(index, mask_record, bbox, polygon_points):
    return Segment(
        id=index,
        polygon=polygon_points,
        bbox=BoundingBox(
            x=int(bbox[0]),
            y=int(bbox[1]),
            width=int(bbox[2]),
            height=int(bbox[3]),
        ),
        predictedIoU=float(mask_record.get("predicted_iou", 0.0)),
        stabilityScore=float(mask_record.get("stability_score", 0.0)),
    )
