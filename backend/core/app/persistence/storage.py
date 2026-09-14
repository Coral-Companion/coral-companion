import os
import cv2
import numpy as np
from google.cloud import storage
import requests
from PIL import Image
from io import BytesIO


BUCKET_NAME = os.environ.get("BUCKET_NAME", "coral-mvp-media")
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "coral-matcher")

def get_storage_client() -> storage.Client:
    return storage.Client(project=GCP_PROJECT)

def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image bytes.")
    return image

def decode_image_stream(file_obj) -> np.ndarray:
    return decode_image_bytes(file_obj.read())

# TODO: make this png for transparency support
def encode_image(image: np.ndarray, image_format: str = ".jpg") -> bytes:
    success, encoded_buffer = cv2.imencode(image_format, image)
    if not success:
        raise ValueError("Failed to encode image for storage upload.")
    return encoded_buffer.tobytes()

def upload_image_bytes_to_bucket(image_bytes: bytes, destination_path: str, content_type: str = "image/jpeg") -> str:
    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_path)
    blob.upload_from_string(image_bytes, content_type=content_type)
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{destination_path}"

def upload_image_to_bucket(image: np.ndarray, destination_path: str, image_format: str = ".jpg", content_type: str = "image/jpeg") -> str:
    encoded_bytes = encode_image(image, image_format)
    return upload_image_bytes_to_bucket(encoded_bytes, destination_path, content_type=content_type)

def save_debug_image(image: np.ndarray, destination_path: str) -> None:
    cv2.imwrite(destination_path, image)

def load_image(url: str) -> np.ndarray:
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return np.array(img)
