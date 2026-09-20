from __future__ import annotations
from uuid import UUID
import logging
from PIL import Image
import base64
import io
import numpy as np
import cv2
from pathlib import Path
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


from app.domain.observation_comparison import ObservationComparison
from app.persistence.observation_repository import ObservationRepository, ObservationSummary
from app.persistence.storage import load_image

from app.analysis.visualization import sobel, laplacian

class AnalysisService:
    """
    Business logic for comparing observations
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.observation_repository = ObservationRepository()

    def analyse_visually(self, id: UUID) -> dict[str, str]:
        """
        performs visual analysis and returns base64 encoded images
        """
        summary = self.observation_repository.find_by_id(id)
        
        images = {}
        if summary:
            masked_image_url = summary.cropped_image_path
            image = load_image(masked_image_url)
            
            sobel_figure: Figure = sobel(image)
            sobel_base64 = self._convert_figure_base64(sobel_figure)
            images["sobel"] = f"data:image/png;base64,{sobel_base64}"
            
            laplacian_figure: Figure = laplacian(image)
            laplacian_base64 = self._convert_figure_base64(laplacian_figure)
            images["laplacian"] = f"data:image/png;base64,{laplacian_base64}"
            
        return images

    def _convert_figure_base64(self, figure):
        """
        Converts the argument into base64.
        <br /><b>Warning sideeffect</b>: closes the figure using plt.close(figure) 
        since this function assumes the figure was created using plt.
        """
        buf = io.BytesIO()
        figure.savefig(buf, format="png", bbox_inches="tight", dpi=300)

        buf.seek(0)
        figure_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        buf.close()
        plt.close(figure)
        return figure_base64
