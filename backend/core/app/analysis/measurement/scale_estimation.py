from .models import TickPositions, RulerScale, ScaleFit, RotatedRuler

from pathlib import Path
import numpy as np
import cv2


class ScaleEstimation:
    """
    Detects repeated interval by detected ticks pattern
    <br />
    <br />
    Produces a debug image showing
    * detected ticks
    * ticks used to establish scale
    * inferred/derived repeating interval
    """
    
    def __init__(self,
        spacing_tolerance: float = 1.0,
        gap_tolerance: float = 2.0,
        scale_tick_tolerance: float = 2.0,
    ) -> None:
        self.spacing_tolerance = spacing_tolerance        
        self.gap_tolerance = gap_tolerance
        self.scale_tick_tolerance = scale_tick_tolerance
        self.spacing_tolerance = 2.0
        self.minimum_cluster_ticks = 3
        self.minimum_group_size = 3
        self.minimum_group_coverage = 0.5

    def estimate_ruler_scale(
        self,
        tick_positions: TickPositions,
        name_for_debug: str | None = None,
        rotated_ruler: RotatedRuler | None = None,
    ) -> RulerScale:
        """
        Estimate pixels-per-mm from the largest locally consistent
        cluster of detected ruler ticks.

        Every detected tick represents one millimeter.

        The algorithm deliberately makes no attempt to reconcile
        different clusters. The largest cluster wins.
        """

        positions = np.asarray(
            tick_positions.positions,
            dtype=np.float64,
        )

        self._validate_scale_input(
            positions
        )

        positions = np.sort(
            positions
        )

        # ---------------------------------------------------------
        # 1. Find locally consistent clusters of neighbouring ticks.
        # ---------------------------------------------------------

        clusters = self._find_tick_clusters(
            positions
        )

        if not clusters:
            raise ValueError(
                "Could not find a sufficiently large cluster of "
                "regularly spaced ticks."
            )

        # ---------------------------------------------------------
        # 2. The cluster containing the most ticks wins.
        # ---------------------------------------------------------

        winning_cluster = max(
            clusters,
            key=len,
        )

        if len(winning_cluster) < self.minimum_cluster_ticks:
            raise ValueError(
                "The largest tick cluster contains too few ticks "
                "to estimate ruler scale."
            )

        # ---------------------------------------------------------
        # 3. Estimate pixels-per-mm from the winning cluster.
        # ---------------------------------------------------------

        cluster_spacings = np.diff(
            winning_cluster
        )

        pixels_per_mm = float(
            np.mean(
                cluster_spacings
            )
        )

        # ---------------------------------------------------------
        # 4. Measure how consistently the cluster follows its
        #    estimated spacing.
        # ---------------------------------------------------------

        spacing_residual = float(
            np.sqrt(
                np.mean(
                    (
                        cluster_spacings
                        - pixels_per_mm
                    ) ** 2
                )
            )
        )

        confidence = self._calculate_scale_confidence(
            spacing_residual=spacing_residual,
            cluster_size=len(winning_cluster),
        )

        result = RulerScale(
            pixels_per_mm=pixels_per_mm,
            confidence=confidence,
            supporting_ticks=np.asarray(
                winning_cluster,
                dtype=np.float64,
            ),
            spacing_residual=spacing_residual,
        )

        if name_for_debug and rotated_ruler:
            self._save_scale_debug_image(
                rotated_ruler=rotated_ruler,
                detected_ticks=positions,
                supporting_ticks=np.asarray(
                    winning_cluster,
                    dtype=np.float64,
                ),
                ruler_scale=result,
                name=name_for_debug,
            )

        return result
    
    
    def _find_tick_clusters(
        self,
        positions: np.ndarray,
    ) -> list[np.ndarray]:
        """
        Group neighbouring detected ticks when their spacing remains
        locally consistent.

        Example:

            positions:
                100  113  126  140  154  180  194

            spacings:
                13   13   14   14   26   14

            with tolerance=1:

                cluster 1:
                    100 113 126 140 154

                cluster 2:
                    180 194

        The comparison is always between neighbouring spacings.
        """

        if positions.size < 2:
            return []

        spacings = np.diff(
            positions
        )

        clusters: list[np.ndarray] = []

        cluster_start = 0

        for spacing_index in range(
            1,
            len(spacings),
        ):
            previous_spacing = (
                spacings[
                    spacing_index - 1
                ]
            )

            current_spacing = (
                spacings[
                    spacing_index
                ]
            )

            spacing_difference = abs(
                current_spacing
                - previous_spacing
            )

            if (
                spacing_difference
                > self.spacing_tolerance
            ):
                cluster_end = (
                    spacing_index
                )

                cluster = positions[
                    cluster_start : cluster_end + 1
                ]

                if len(cluster) >= (
                    self.minimum_cluster_ticks
                ):
                    clusters.append(
                        cluster.copy()
                    )

                cluster_start = (
                    spacing_index
                )

        # ---------------------------------------------------------
        # Add the final cluster.
        # ---------------------------------------------------------

        cluster = positions[
            cluster_start:
        ]

        if len(cluster) >= (
            self.minimum_cluster_ticks
        ):
            clusters.append(
                cluster.copy()
            )

        return clusters
    
    def _validate_scale_input(
        self,
        positions: np.ndarray,
    ) -> None:
        if positions.ndim != 1:
            raise ValueError(
                "Tick positions must be a 1D array."
            )

        if positions.size < 3:
            raise ValueError(
                "At least three tick positions are required."
            )

        if not np.all(
            np.isfinite(positions)
        ):
            raise ValueError(
                "Tick positions contain non-finite values."
            )

        if np.any(
            np.diff(
                np.sort(positions)
            ) <= 0
        ):
            raise ValueError(
                "Tick positions must be unique."
            )
    
    def _calculate_scale_confidence(
        self,
        spacing_residual: float,
        cluster_size: int,
    ) -> float:
        """
        Descriptive confidence based only on local spacing consistency
        and the number of supporting ticks.
        """

        if cluster_size < 3:
            return 0.0

        # Perfectly regular spacing -> 1.0.
        #
        # At 1 pixel RMS residual, confidence reaches zero.
        residual_score = max(
            0.0,
            1.0 - spacing_residual,
        )

        # 3 ticks is the minimum useful cluster.
        # Additional ticks increase confidence, with diminishing returns.
        size_score = min(
            1.0,
            cluster_size / 10.0,
        )

        return float(
            residual_score * size_score
        )
        
    def _save_scale_debug_image(
        self,
        rotated_ruler: RotatedRuler,
        detected_ticks: np.ndarray,
        supporting_ticks: np.ndarray,
        ruler_scale: RulerScale,
        name: str,
    ) -> None:
        """
        Draw the selected tick cluster in green and all other detected
        ticks in red.
        """

        image = rotated_ruler.image

        if image is None or image.size == 0:
            return

        debug_image = image.copy()

        height = debug_image.shape[0]

        supporting_positions = {
            int(round(position))
            for position in supporting_ticks
        }

        # ---------------------------------------------------------
        # All detected ticks.
        # ---------------------------------------------------------

        for position in detected_ticks:

            x = int(
                round(position)
            )

            if x in supporting_positions:
                continue

            cv2.line(
                debug_image,
                (x, 0),
                (x, height - 1),
                (0, 0, 255),
                2,
            )

        # ---------------------------------------------------------
        # Winning cluster.
        # ---------------------------------------------------------

        for position in supporting_ticks:

            x = int(
                round(position)
            )

            cv2.line(
                debug_image,
                (x, 0),
                (x, height - 1),
                (0, 255, 0),
                2,
            )

        # ---------------------------------------------------------
        # Information.
        # ---------------------------------------------------------

        text = (
            f"{ruler_scale.pixels_per_mm:.2f} px/mm"
            f" | ticks: {len(supporting_ticks)}"
            f" | residual: "
            f"{ruler_scale.spacing_residual:.2f}px"
        )

        cv2.putText(
            debug_image,
            text,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
        debug_dir = Path(
            "test/analysis/measurement/debug"
        )

        debug_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            debug_dir
            / f"{name}_stage_5_scale_estimation.png"
        )

        cv2.imwrite(
            str(output_path),
            debug_image,
        )
