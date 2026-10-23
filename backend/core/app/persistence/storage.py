import os
import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from botocore.client import BaseClient
import boto3
import logging
from urllib.parse import quote

BUCKET_NAME = os.environ.get("BUCKET_NAME", "coral-companion-media")
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_PUBLIC_BASE_URL = os.environ.get("R2_PUBLIC_BASE_URL", "https://media.coralcompanion.earth")

logger = logging.getLogger(__name__)

def get_storage_client() -> BaseClient:
    """Create an S3-compatible Cloudflare R2 client."""
    if not R2_ACCOUNT_ID:
        raise RuntimeError("R2_ACCOUNT_ID is not configured.")
    if not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        raise RuntimeError("R2 credentials are not configured.")

    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )

def decode_image_bytes(image_bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image bytes.")
    return image

# TODO: make this png for transparency support
def encode_image(image: np.ndarray, image_format: str = ".jpg") -> bytes:
    success, encoded_buffer = cv2.imencode(image_format, image)
    if not success:
        raise ValueError("Failed to encode image for storage upload.")
    return encoded_buffer.tobytes()

def upload_image_bytes_to_bucket(
    image_bytes: bytes,
    destination_path: str,
    content_type: str = "image/jpeg",
) -> str:
    """Upload image bytes to R2 and return the public URL."""
    if not R2_PUBLIC_BASE_URL:
        raise RuntimeError("R2_PUBLIC_BASE_URL is not configured.")

    if not destination_path or destination_path.startswith("/"):
        raise ValueError("destination_path must be a relative object key.")

    client = get_storage_client()

    logger.debug(f"Uploading image to R2: bucket={BUCKET_NAME}, key={destination_path}, bytes={len(image_bytes)}")
    client.put_object(Bucket=BUCKET_NAME, Key=destination_path, Body=image_bytes, ContentType=content_type)

    encoded_path = quote(destination_path, safe="/")
    url = f"{R2_PUBLIC_BASE_URL}/{encoded_path}"
    logger.debug(f"R2 upload complete: {url}")
    return url

def upload_image_to_bucket(image: np.ndarray, destination_path: str, image_format: str = ".jpg", content_type: str = "image/jpeg") -> str:
    encoded_bytes = encode_image(image, image_format)
    return upload_image_bytes_to_bucket(encoded_bytes, destination_path, content_type=content_type)

def save_debug_image(image: np.ndarray, destination_path: str) -> None:
    cv2.imwrite(destination_path, image)

def load_image(url: str) -> np.ndarray:
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return np.array(img)
