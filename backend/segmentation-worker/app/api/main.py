from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, HTTPException, Request, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from dataclasses import asdict

import cv2
import numpy as np
import torch

import logging
from pathlib import Path

from third_party.coralscop.segment_anything import SamAutomaticMaskGenerator, sam_model_registry
from app.utils.performance_profiler import performance_stage, log_memory
from .models import Segment, BoundingBox, Point, SegmentationResult

model_type = "vit_b"

# Piggyback on uvicorn logger infrastructure
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    The model is loaded once when the container boots,
    preventing cold-start penalties on every request.
    """
    logger.info("Initializing Segmentation Worker")
    
    checkpoint_path = (
        Path(__file__).resolve().parents[2]
        / "third_party"
        / "coralscop"
        / "checkpoints"
        / "vit_b_coralscop.pth"
    )
    
    # Determine device (prepare for your future GPU transition)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading CoralSCOP onto {device}...")
    try:
        sam = sam_model_registry[model_type](checkpoint=str(checkpoint_path))
        sam.to(device=device)
        
        # TODO: make arguments parameterizable: points_per_side, layers, points_per_batch
        app.state.mask_generator = SamAutomaticMaskGenerator(
            model=sam,
            points_per_side=10,
            pred_iou_thresh=0.75,
            stability_score_thresh=0.75,
            crop_n_layers=0,
            crop_n_points_downscale_factor=2,
            min_mask_region_area=100,
            points_per_batch=32
        )
        
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.exception(f"Failed to load model: {e}", e)
        raise e

    # Serve requests while in this state
    yield

    # Teardown logic when the container scales to zero or shuts down
    print("Shutting down ML Worker, clearing memory...")
    mask_generator = {}
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(title="Coral Monitoring ML Worker", lifespan=lifespan)

@app.get("/health")
async def health_check(request: Request):
    """Lightweight endpoint for container health probes."""
    return {
        "status": "healthy",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "model_loaded": get_mask_generator(request)
    }


@app.post("/api/segment")
async def segment_image(request: Request, file: UploadFile = File(...)):
    """Receives an image, runs inference, and returns masks."""
    mask_generator = get_mask_generator(request)
    if mask_generator is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")

    try:
        image, rgb = await prepare_image(file)
        
        with performance_stage("Segmentation"):
            masks = mask_generator.generate(rgb)

        segments: list[Segment] = []
        for index, mask_record in enumerate(masks):
            segmentation = mask_record.get("segmentation")
            bbox = mask_record.get("bbox", [0, 0, 0, 0])
            polygon_points = []
            if isinstance(segmentation, np.ndarray):
                mask = segmentation
                mask = (mask > 0).astype(np.uint8) * 255
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                if contours:
                    contour = max(contours, key=cv2.contourArea)
                    polygon_points = [Point(int(x), int(y)) for x, y in contour.reshape(-1, 2)]

            segments.append(
                build_segment(index, mask_record, bbox, polygon_points)
            )

        height, width = image.shape[:2]

        return JSONResponse(
            content={
                "result": jsonable_encoder(asdict(SegmentationResult(
                        image_width=int(width),
                        image_height=int(height),
                        segments=segments
                    )))
            }
        )

    except Exception as e:
        logger.exception("An error occurred", e)
        raise HTTPException(status_code=500, detail=str(e))

def get_mask_generator(request):
    return getattr(request.app.state, "mask_generator", None)

async def prepare_image(file):
    file_bytes = await file.read()
    file_ndarray = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(file_ndarray, cv2.IMREAD_COLOR)
    if image is None:
        logger.warning("Decoding image resulted in 'None'")
        raise HTTPException(status_code=400, detail="Invalid image file format.")
    elif len(image.shape) != 3:
        logger.warning(f"Expected BGR image. Received image with shape length {len(image.shape)}")
        raise HTTPException(400, "Image dimensions off. Expected BGR image")

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.imwrite("test.jpg", image)
    return image,rgb

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