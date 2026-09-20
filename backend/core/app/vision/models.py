from dataclasses import dataclass

import numpy as np

@dataclass(slots=True)
class MaskResult:
    masked_image: np.ndarray
