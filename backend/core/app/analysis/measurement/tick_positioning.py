from .models import TickSignals, TickPositions, RotatedRuler
from dataclasses import dataclass
from collections.abc import Sequence

import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt



class TickPositioning:

    def find_tick_positions(
        self,
        detection: TickSignals,
        name_for_debug: str | None = None,
        rotated_ruler_for_debug: RotatedRuler | None = None,
    ) -> TickPositions:
        """
        Converts the 1D tick signal into ordered tick positions.

        The detection stage gives us a continuous signal and a relative
        threshold. This stage finds reliable peaks in that signal, estimates
        the dominant spacing between neighbouring ticks, and removes peaks
        that are likely duplicate responses from the same physical tick.

        Missing ticks are deliberately not inferred yet.
        """

        signal = np.asarray(detection.signal, dtype=np.float32)

        if signal.ndim != 1:
            raise ValueError(
                "Tick signal must be a one-dimensional array."
            )

        if signal.size == 0:
            raise ValueError(
                "Tick signal must not be empty."
            )

        if not np.isfinite(signal).all():
            raise ValueError(
                "Tick signal contains non-finite values."
            )

        threshold = float(detection.threshold)

        # ------------------------------------------------------------
        # 1. Find local peaks above the detection threshold
        # ------------------------------------------------------------

        candidate_positions, candidate_strengths = (
            self._find_candidate_peaks(
                signal=signal,
                threshold=threshold,
            )
        )

        if candidate_positions.size == 0:
            return TickPositions(
                positions=np.empty(0, dtype=np.float32),
                strengths=np.empty(0, dtype=np.float32),
            )

        if candidate_positions.size == 1:
            return TickPositions(
                positions=candidate_positions.astype(np.float32),
                strengths=candidate_strengths.astype(np.float32),
            )

        # ------------------------------------------------------------
        # 2. Estimate the dominant tick spacing
        # ------------------------------------------------------------

        spacing = self._estimate_tick_spacing(
            candidate_positions
        )

        if spacing <= 0:
            return TickPositions(
                positions=candidate_positions.astype(np.float32),
                strengths=candidate_strengths.astype(np.float32),
            )

        # ------------------------------------------------------------
        # 3. Remove duplicate peaks belonging to the same tick
        # ------------------------------------------------------------

        positions, strengths = self._remove_duplicate_peaks(
            positions=candidate_positions,
            strengths=candidate_strengths,
            expected_spacing=spacing,
        )
        
        positions = TickPositions(
            positions=positions.astype(np.float32),
            strengths=strengths.astype(np.float32),
        )
        
        if name_for_debug and rotated_ruler_for_debug:
            self.save_tick_positioning_debug_image(rotated_ruler_for_debug, detection, positions, name_for_debug)

        return positions

    # ------------------------------------------------------------------
    # Candidate detection
    # ------------------------------------------------------------------

    @staticmethod
    def _find_candidate_peaks(
        signal: np.ndarray,
        threshold: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Finds local maxima whose signal strength exceeds the threshold.

        A sample is considered a peak when it is:
        1. above the threshold,
        2. at least as high as its left neighbour,
        3. higher than its right neighbour.
        """

        peak_positions: list[int] = []
        peak_strengths: list[float] = []

        for index in range(1, len(signal) - 1):
            value = signal[index]

            if value < threshold:
                continue

            is_higher_than_left = value >= signal[index - 1]
            is_higher_than_right = value > signal[index + 1]

            if is_higher_than_left and is_higher_than_right:
                peak_positions.append(index)
                peak_strengths.append(float(value))

        return (
            np.asarray(peak_positions, dtype=np.int32),
            np.asarray(peak_strengths, dtype=np.float32),
        )

    # ------------------------------------------------------------------
    # Spacing estimation
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_tick_spacing(
        positions: np.ndarray,
    ) -> float:
        """
        Estimates the dominant spacing between candidate ticks.
        """

        if positions.size < 2:
            return 0.0

        positions = np.sort(positions.astype(np.float32))

        distances = np.diff(positions)

        if distances.size == 0:
            return 0.0

        # Ignore zero-distance duplicates.
        distances = distances[distances > 0]

        if distances.size == 0:
            return 0.0

        # Robust estimate:
        #
        # Duplicate detections from a single tick can create very small
        # distances. The real tick spacing should therefore normally be
        # somewhere in the larger part of the distribution.
        #
        # Start with the median of the upper half of neighbouring distances.
        median_distance = float(np.median(distances))

        if median_distance <= 0:
            return 0.0

        # Keep distances that are reasonably close to the median.
        #
        # This is intentionally permissive. We don't want this stage to
        # reject legitimate spacing variation caused by perspective,
        # distortion, or imperfect detection.
        lower = median_distance * 0.5
        upper = median_distance * 1.5

        plausible = distances[
            (distances >= lower)
            & (distances <= upper)
        ]

        if plausible.size == 0:
            return median_distance

        return float(np.median(plausible))

    # ------------------------------------------------------------------
    # Duplicate removal
    # ------------------------------------------------------------------

    @staticmethod
    def _remove_duplicate_peaks(
        positions: np.ndarray,
        strengths: np.ndarray,
        expected_spacing: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Collapses multiple peaks that are too close to represent separate
        ruler ticks.

        Within each cluster, the strongest peak is retained.
        """

        if positions.size <= 1:
            return positions, strengths

        order = np.argsort(positions)

        positions = positions[order]
        strengths = strengths[order]

        # Anything substantially closer than a normal tick spacing is
        # considered part of the same candidate cluster.
        duplicate_distance = expected_spacing * 0.5

        kept_positions: list[int] = []
        kept_strengths: list[float] = []

        cluster_positions: list[int] = []
        cluster_strengths: list[float] = []

        for position, strength in zip(
            positions,
            strengths,
        ):
            position = int(position)
            strength = float(strength)

            if not cluster_positions:
                cluster_positions.append(position)
                cluster_strengths.append(strength)
                continue

            distance = position - cluster_positions[-1]

            if distance <= duplicate_distance:
                cluster_positions.append(position)
                cluster_strengths.append(strength)
            else:
                strongest_index = int(
                    np.argmax(cluster_strengths)
                )

                kept_positions.append(
                    cluster_positions[strongest_index]
                )
                kept_strengths.append(
                    cluster_strengths[strongest_index]
                )

                cluster_positions = [position]
                cluster_strengths = [strength]

        # Flush final cluster.
        if cluster_positions:
            strongest_index = int(
                np.argmax(cluster_strengths)
            )

            kept_positions.append(
                cluster_positions[strongest_index]
            )
            kept_strengths.append(
                cluster_strengths[strongest_index]
            )

        return (
            np.asarray(kept_positions, dtype=np.int32),
            np.asarray(kept_strengths, dtype=np.float32),
        )
        
    def save_tick_positioning_debug_image(
        self,
        rotated_ruler: RotatedRuler,
        signals: TickSignals,
        positions: TickPositions,
        name: str,
    ) -> None:
        """
        Saves a debug visualization of tick detection and positioning.

        Top:
            Rotated ruler with candidate peaks and final tick positions.

        Bottom:
            1D tick signal with threshold and candidate/final positions.

        Candidate peaks and final positions are intentionally shown separately
        so that positioning decisions can be visually inspected.
        """

        debug_dir = Path(
            "test/analysis/measurement/debug"
        )

        debug_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            debug_dir
            / f"{name}_stage_4_tick_positioning.png"
        )

        image = rotated_ruler.image

        # ------------------------------------------------------------
        # Prepare image for matplotlib
        # ------------------------------------------------------------

        if image.ndim == 3:
            # OpenCV image is BGR, matplotlib expects RGB.
            display_image = image[:, :, ::-1]
        else:
            display_image = image

        signal = np.asarray(
            signals.signal,
            dtype=np.float32,
        )

        final_positions = np.asarray(
            positions.positions,
            dtype=np.float32,
        )

        strengths = np.asarray(
            positions.strengths,
            dtype=np.float32,
        )

        # ------------------------------------------------------------
        # Create figure
        # ------------------------------------------------------------

        fig, (image_ax, signal_ax) = plt.subplots(
            2,
            1,
            figsize=(16, 8),
            gridspec_kw={
                "height_ratios": [2, 1],
            },
        )

        # ============================================================
        # TOP: ruler image
        # ============================================================

        image_ax.imshow(display_image)

        image_ax.set_title(
            "Tick positioning"
        )

        image_ax.set_xlim(
            0,
            image.shape[1],
        )

        image_ax.set_ylim(
            image.shape[0],
            0,
        )

        # Final positions
        for x, strength in zip(
            final_positions,
            strengths,
        ):
            image_ax.axvline(
                x=float(x),
                linestyle="-",
                linewidth=2.0,
                alpha=0.9,
                label="positioned tick",
            )

            image_ax.text(
                float(x),
                10,
                f"{strength:.2f}",
                rotation=90,
                verticalalignment="top",
                horizontalalignment="right",
                fontsize=8,
            )

        # Avoid duplicate legend entries from every line.
        handles, labels = image_ax.get_legend_handles_labels()

        unique = dict(
            zip(labels, handles)
        )

        image_ax.legend(
            unique.values(),
            unique.keys(),
            loc="upper right",
        )

        image_ax.set_xlabel(
            "x position [px]"
        )

        image_ax.set_ylabel(
            "y position [px]"
        )

        # ============================================================
        # BOTTOM: signal
        # ============================================================

        x = np.arange(
            signal.size
        )

        signal_ax.plot(
            x,
            signal,
            linewidth=1.5,
            label="signal",
        )

        signal_ax.axhline(
            y=signals.threshold,
            linestyle="--",
            linewidth=1.5,
            label=f"threshold ({signals.threshold:.2f})",
        )

        # Final positions
        if final_positions.size > 0:
            # Positions are currently integer-like, but keeping this robust
            # also makes the visualization work if we later infer subpixel
            # positions.
            valid = (
                (final_positions >= 0)
                & (final_positions < signal.size)
            )

            final_x = final_positions[valid]

            final_y = np.interp(
                final_x,
                x,
                signal,
            )

            signal_ax.scatter(
                final_x,
                final_y,
                s=60,
                marker="x",
                linewidths=2,
                label="positioned ticks",
                zorder=4,
            )

        signal_ax.set_title(
            "Tick signal"
        )

        signal_ax.set_xlabel(
            "x position [px]"
        )

        signal_ax.set_ylabel(
            "signal strength"
        )

        signal_ax.set_xlim(
            0,
            signal.size - 1,
        )

        signal_ax.legend()

        fig.tight_layout()

        fig.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(fig)