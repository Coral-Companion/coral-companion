from __future__ import annotations
from uuid import UUID
import logging

from app.domain.observation_comparison import ObservationComparison
from app.persistence.observation_repository import ObservationRepository, ObservationSummary
from app.analysis.metrics import compute_metrics, sobel_image
from app.persistence.storage import load_image
from app.domain.models import Metric


class ComparisonService:
    """
    Business logic for comparing observations
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.observation_repository = ObservationRepository()

    def compare_observations(self, ids: list[UUID]) -> list[ObservationComparison]:
        """
        compares observations pair-wise in order of the given list. The percentage changes of the first result will be 0.
        """
        summaries = self.observation_repository.find_summaries_by_ids(ids)
        
        comparisons: list[ObservationComparison] = []

        # enable O(1) lookups
        previous_metrics_lookup = {}

        for i, summary in enumerate(summaries):
            image = load_image(summary.image_path)
            metrics_dict = compute_metrics(image)
            
            current_metrics_lookup = {}
            metrics = []
            
            # extract and flatten metrics while simultaneously calculating percentages
            for category in metrics_dict.values():
                for name, value in category.items():
                    float_val = float(value)
                    current_metrics_lookup[name] = float_val
                    
                    change = 0
                    if i > 0 and name in previous_metrics_lookup:
                        previous_value = previous_metrics_lookup[name]
                        if previous_value != 0:
                            change = ((float_val - previous_value) / previous_value) * 100
                        else:
                            change = 0.0
                    
                    metrics.append(Metric(id=name, value=float_val, changePercentage=change))
                    
            baseline = summaries[i - 1] if i > 0 else None
            
            comparisons.append(ObservationComparison(
                baseline=baseline, 
                observation=summary, 
                metrics=metrics
            ))
            
            previous_metrics_lookup = current_metrics_lookup

        return comparisons
