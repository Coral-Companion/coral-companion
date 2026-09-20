import os
from pathlib import Path

import cv2
import numpy as np

from app.embedding.embedding import EmbeddingService

    # ---------------------------------------------------------------------------

    # Configuration

    # ---------------------------------------------------------------------------

REFERENCE_IMAGE_PATH = os.getenv(
"ROTATION_TEST_REFERENCE",
"dev_fixtures/islalarga_c015/20260718_1504.jpg",
)

QUERY_IMAGE_PATH = os.getenv(
"ROTATION_TEST_QUERY",
"dev_fixtures/islalarga_c015/20260718_1509.jpg",
)

    # ---------------------------------------------------------------------------

    # Helpers

    # ---------------------------------------------------------------------------

def rotate_image(image, angle):
    """
    Rotate an OpenCV image by 0, 90, 180, or 270 degrees.
    """

    if angle == 0:
        return image.copy()

    if angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    if angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)

    if angle == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    raise ValueError(f"Unsupported rotation angle: {angle}")
    

def cosine_similarity(vector_a, vector_b):
    """
    Calculate cosine similarity between two embedding vectors.
    """
    vector_a = np.asarray(vector_a, dtype=np.float32)
    vector_b = np.asarray(vector_b, dtype=np.float32)

    vector_a /= np.linalg.norm(vector_a)
    vector_b /= np.linalg.norm(vector_b)

    return float(np.dot(vector_a, vector_b))
    

def calculate_top_two_mean(scores):
    """
    Calculate the mean of the two highest similarity scores.
    """
    
    top_two = sorted(scores, reverse=True)[:2]

    return float(np.mean(top_two))
    

def load_image(path):
    """
    Load an image and fail with a useful error message.
    """
    
    path = Path(path)

    assert path.exists(), (
        f"Image does not exist: {path.resolve()}"
    )

    image = cv2.imread(str(path))

    assert image is not None, (
        f"OpenCV could not load image: {path.resolve()}"
    )

    return image
    

    # ---------------------------------------------------------------------------

    # Test

    # ---------------------------------------------------------------------------

def test_same_colony_rotation_invariance():
    """
    Compare two different images of the same coral colony.

    
    The reference image is embedded once.

    The query image is embedded at:

        0°
        90°
        180°
        270°

    Each query embedding is compared to the reference embedding.

    This tells us whether rotation augmentation could improve matching
    between genuinely different photos of the same colony.
    """

    reference_image = load_image(REFERENCE_IMAGE_PATH)
    query_image = load_image(QUERY_IMAGE_PATH)

    embedding_service = EmbeddingService()

    # -----------------------------------------------------------------------
    # Generate reference embedding
    # -----------------------------------------------------------------------

    reference_embedding = (
        embedding_service.generate_vector_embedding(
            reference_image
        )
    )

    # -----------------------------------------------------------------------
    # Generate rotated query embeddings
    # -----------------------------------------------------------------------

    rotations = [0, 90, 180, 270]

    similarity_scores = {}

    for angle in rotations:

        rotated_query = rotate_image(
            query_image,
            angle,
        )

        query_embedding = (
            embedding_service.generate_vector_embedding(
                rotated_query
            )
        )

        similarity_scores[angle] = cosine_similarity(
            reference_embedding,
            query_embedding,
        )

    scores = list(similarity_scores.values())

    best_rotation = max(
        similarity_scores,
        key=similarity_scores.get,
    )

    best_similarity = similarity_scores[best_rotation]

    baseline_similarity = similarity_scores[0]

    top_two_mean = calculate_top_two_mean(scores)

    all_rotation_mean = float(np.mean(scores))

    improvement_over_baseline = (
        best_similarity - baseline_similarity
    )

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------

    print()
    print("=" * 70)
    print("SAME-COLONY ROTATION MATCHING TEST")
    print("=" * 70)

    print(f"Reference: {REFERENCE_IMAGE_PATH}")
    print(f"Query:     {QUERY_IMAGE_PATH}")

    print()
    print("Similarity between reference image and rotated query image:")
    print("-" * 70)

    for angle in rotations:
        print(
            f"{angle:>3}° rotation: "
            f"{similarity_scores[angle]:.4f}"
        )

    print()
    print("-" * 70)

    print(
        f"Baseline (0°):       "
        f"{baseline_similarity:.4f}"
    )

    print(
        f"Rotation-aware max:  "
        f"{best_similarity:.4f}"
    )

    print(
        f"Best rotation:       "
        f"{best_rotation}°"
    )

    print(
        f"Top-2 mean:          "
        f"{top_two_mean:.4f}"
    )

    print(
        f"All-rotation mean:   "
        f"{all_rotation_mean:.4f}"
    )

    print(
        f"Improvement:         "
        f"{improvement_over_baseline:+.4f}"
    )

    print("=" * 70)
    print()

    # -----------------------------------------------------------------------
    # Basic sanity checks
    # -----------------------------------------------------------------------

    assert len(similarity_scores) == 4

    assert all(
        -1.0 <= score <= 1.0
        for score in similarity_scores.values()
    )
    
