import pytest
import numpy as np
import cv2
from app.embedding.embedding import EmbeddingService

def test_resnet_feature_vector_dimensions():
    """
    Creates an artificial 300x300 canvas to ensure the PyTorch 
    engine extracts exactly 512 descriptive parameters.
    """
    # Create mock canvas matrix
    mock_coral_canvas = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    
    # Generate signature array
    vector_output = EmbeddingService().generate_vector_embedding(mock_coral_canvas)
    
    assert isinstance(vector_output, list)
    assert len(vector_output) == 512
    assert isinstance(vector_output[0], float)


