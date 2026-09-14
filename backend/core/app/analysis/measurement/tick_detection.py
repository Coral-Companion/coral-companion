import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from collections.abc import Callable

from .models import RotatedRuler, TickSignals, TickSignalScore

class TickDetection:
    """
    Summary
        Detects the ticks on the given ruler. Does not qualify
        units, just identifies signals (in 1D) representing the strength of
        tick-like structures along the horizontal ruler axis. 
        Technically, the following question is asked: How much brightness change exists at each x-position along the ruler?
        And it is answered as follows:
        1. Calculate sobel of every x-column on an image containing the masked ruler
        2. Apply a function to all sobel values to reduce x-columns into single values (by default median)
        3. Pick the strongest of these values using a threshold (by default 85th percentile)

    Args:
        sobel_kernel_size (int, optional): Small numbers are more sensitive to small artifacts.
            Larger numbers allow for more smoothing (e.g in case of lot of noise). Must be odd. Defaults to 3.
        threshold_percentile (float, optional): Threshold of when to count a signal to be strong 
            enough to become a tick candidate. Range: (0, 100). Defaults to 85.0
        maximum_tick_width (int, optional): Threshold of how wide a tick can be in pixels. Defaults to 20
        signal_aggregation: The function to be used to aggregate vertical signals (must take one argument np.ndarray). E.g. to use percentile:
            functools.partial(np.percentile, q=75). Defaults to np.median
        name_for_debug (str | None, optional): _description_. Defaults to None.
    """
    
    def __init__(self,
        sobel_kernel_size: int = 3,
        threshold_percentile: float = 85.0,
        maximum_tick_width: int = 20,
        signal_aggregation: Callable[[np.ndarray], float] = np.median,
    ):
        self.sobel_kernel_size = sobel_kernel_size
        self.threshold_percentile = threshold_percentile
        self.maximum_tick_width = maximum_tick_width
        self.signal_aggregation = signal_aggregation
    
    
    def detect_ticks(
        self,
        rotated_ruler: RotatedRuler,
        name_for_debug: str | None = None,
    ) -> TickSignals:
        if rotated_ruler.image is None or rotated_ruler.image.size == 0:
            raise ValueError("Rotated ruler contains an empty image.")

        if rotated_ruler.mask is None or rotated_ruler.mask.size == 0:
            raise ValueError("Rotated ruler contains an empty mask.")

        image = rotated_ruler.image
        mask = rotated_ruler.mask

        if mask.shape != image.shape[:2]:
            raise ValueError(
                "Rotated ruler mask does not match image dimensions."
            )

        # ---------------------------------------------------------
        # 1. Convert image to grayscale
        # ---------------------------------------------------------

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ---------------------------------------------------------
        # 2. Determine the actual ruler region from the mask
        # ---------------------------------------------------------

        ys, xs = np.where(mask > 0)

        if len(xs) == 0:
            raise ValueError("Rotated ruler mask is empty.")

        x_min = int(xs.min())
        x_max = int(xs.max())
        y_min = int(ys.min())
        y_max = int(ys.max())

        ruler_gray = gray[y_min : y_max + 1, x_min : x_max + 1]
        ruler_mask = mask[y_min : y_max + 1, x_min : x_max + 1]

        # ---------------------------------------------------------
        # 3. Split the ruler vertically into top and bottom regions - ignore middle third where the numbers live.
        # ---------------------------------------------------------

        ruler_height = ruler_gray.shape[0]

        third = ruler_height // 3

        top_gray = ruler_gray[:third]
        top_mask = ruler_mask[:third]

        bottom_gray = ruler_gray[third*2:]
        bottom_mask = ruler_mask[third*2:]

        # ---------------------------------------------------------
        # 4. Calculate vertical edge response
        # ---------------------------------------------------------
        #
        # Ticks are approximately vertical.
        #
        # Therefore we want a gradient in the X direction:
        #
        #       tick
        #        │
        #        │
        #        │
        #
        #      ← x →
        #
        # A vertical tick produces strong changes along X.
        #
        # We deliberately do not use the raw brightness signal.
        # This makes the detector much less sensitive to the overall
        # brightness of an image.

        top_gradient = cv2.Sobel(
            top_gray,
            cv2.CV_32F,
            dx=1,
            dy=0,
            ksize=self.sobel_kernel_size,
        )

        bottom_gradient = cv2.Sobel(
            bottom_gray,
            cv2.CV_32F,
            dx=1,
            dy=0,
            ksize=self.sobel_kernel_size,
        )

        top_gradient = np.abs(top_gradient)
        bottom_gradient = np.abs(bottom_gradient)

        # ---------------------------------------------------------
        # 5. Ignore pixels outside the ruler
        # ---------------------------------------------------------

        top_gradient[top_mask == 0] = 0
        bottom_gradient[bottom_mask == 0] = 0

        # ---------------------------------------------------------
        # 6. Collapse each bottom and top third into a 1D signal
        # ---------------------------------------------------------
        #
        # Defaults to median so that the signal
        # does not simply become stronger when more ruler pixels are
        # present in a column. Can be controlled by passing signal_aggregation
        # in constructor
        #
        # The median is also reasonably resistant to isolated noise.

        top_signal = self._collapse_vertical_gradient(
            top_gradient,
            top_mask,
        )

        bottom_signal = self._collapse_vertical_gradient(
            bottom_gradient,
            bottom_mask,
        )

        # ---------------------------------------------------------
        # 7. Normalize each signal independently
        # ---------------------------------------------------------
        #
        # This makes the detector relative to this particular image.
        #
        # We intentionally avoid:
        #
        #     threshold = 50
        #
        # because absolute gradient values depend heavily on exposure,
        # illumination and image processing.
        #
        # Instead, the signal is normalized using robust statistics.

        top_signal = self._normalize_tick_signal(top_signal)
        bottom_signal = self._normalize_tick_signal(bottom_signal)

        # ---------------------------------------------------------
        # 8. Select the signal that looks most like ruler ticks
        # ---------------------------------------------------------
        #
        # We intentionally do not combine the two signals.
        #
        # Only one of the top/bottom thirds contains the metric
        # tick marks. The middle third contains mostly ruler text
        # and other visual structure and is particularily uninteresting.
        #
        # We therefore score both signals based on:
        #
        #   1. number of candidate peaks
        #   2. regularity of the spacing between those peaks
        #

        top_threshold = self._calculate_tick_threshold(
            top_signal
        )

        bottom_threshold = self._calculate_tick_threshold(
            bottom_signal
        )

        top_peaks = self._find_tick_candidates(
            top_signal,
            top_threshold,
        )

        bottom_peaks = self._find_tick_candidates(
            bottom_signal,
            bottom_threshold,
        )

        top_score = self._score_tick_signal(
            top_peaks
        )

        bottom_score = self._score_tick_signal(
            bottom_peaks
        )

        if top_score.score > bottom_score.score:
            selected_signal = top_signal
            selected_threshold = top_threshold
            selected_peaks = top_peaks
            selected_region = "top"

        else:
            selected_signal = bottom_signal
            selected_threshold = bottom_threshold
            selected_peaks = bottom_peaks
            selected_region = "bottom"

        # ---------------------------------------------------------
        # 9. Selected signal
        # ---------------------------------------------------------
        #
        # From this point onwards, the pipeline only works with
        # the signal that appears to contain the actual ticks.
        #
        # We deliberately do not carry the rejected signal forward.

        signal = selected_signal
        threshold = selected_threshold

        # ---------------------------------------------------------
        # 10. Create TickSignals
        # ---------------------------------------------------------

        signals = TickSignals(
            signal=signal,
            threshold=threshold,
        )

        # ---------------------------------------------------------
        # 11. Create result
        # ---------------------------------------------------------

        if name_for_debug:
            self._save_debug_image(
                rotated_ruler=rotated_ruler,
                signals=signals,
                candidate_peaks=selected_peaks,
                selected_region=selected_region,
                top_score=top_score.score,
                bottom_score=bottom_score.score,
                name=name_for_debug,
            )

        return signals
    
    
    def _collapse_vertical_gradient(
        self,
        gradient: np.ndarray,
        mask: np.ndarray,
    ) -> np.ndarray:
        """
        Collapse a 2D vertical-edge response into a 1D horizontal signal.
        """
        height, width = gradient.shape
        signal = np.zeros(width, dtype=np.float32)

        for x in range(width):
            values = gradient[:, x][mask[:, x] > 0]

            if values.size > 0:
                signal[x] = self.signal_aggregation(values)

        return signal
    
    
    def _normalize_tick_signal(
        self,
        signal: np.ndarray,
    ) -> np.ndarray:
        """
        Robustly normalize a tick signal to approximately [0, 1].

        Uses percentile statistics rather than absolute intensity so that
        the resulting signal is relative to the current image.
        """

        positive = signal[signal > 0]

        if positive.size == 0:
            return np.zeros_like(signal)

        low = float(np.percentile(positive, 10.0))
        high = float(np.percentile(positive, 95.0))

        if high <= low:
            return np.zeros_like(signal)

        normalized = (signal - low) / (high - low)

        return np.clip(
            normalized,
            0.0,
            1.0,
        )
        
    def _calculate_tick_threshold(
        self,
        signal: np.ndarray,
    ) -> float:
        """
        Calculates a relative threshold from an already normalized
        tick signal.
        """

        positive = signal[signal > 0]

        if positive.size == 0:
            return 0.0

        return float(
            np.percentile(
                positive,
                self.threshold_percentile,
            )
        )
        
    def _find_tick_candidates(
        self,
        signal: np.ndarray,
        threshold: float,
    ) -> np.ndarray:
        """
        Finds candidate tick positions from a 1D signal.

        Each contiguous above-threshold region contributes one candidate:
        the position of its strongest response.

        Returns:
            1D array containing candidate x positions.
        """

        if signal.size == 0:
            return np.empty(
                0,
                dtype=np.int32,
            )

        # turns signal into boolean array with all above threshold = True
        above_threshold = signal >= threshold

        if not np.any(above_threshold):
            return np.empty(
                0,
                dtype=np.int32,
            )

        # boolean[] -> int[], more precisely array of 1/0
        transitions = np.diff(
            above_threshold.astype(np.int8)
        )

        # finds the starting border where the signal is above threshold
        starts = (
            np.flatnonzero(
                transitions == 1
            ) + 1
        )

        # finds the ending border where the signal is again below threshold
        ends = (
            np.flatnonzero(
                transitions == -1
            ) + 1
        )

        if above_threshold[0]:
            starts = np.insert(
                starts,
                0,
                0,
            )

        if above_threshold[-1]:
            ends = np.append(
                ends,
                len(signal),
            )

        peaks = []

        # identfies the center in a region of strong signals (above threshold)
        for start, end in zip(starts, ends):
            if end <= start:
                continue
            
            if end - start > self.maximum_tick_width:
                continue

            peak_offset = int(
                np.argmax(
                    signal[start:end]
                )
            )

            peak_position = start + peak_offset

            peaks.append(
                peak_position
            )

        return np.asarray(
            peaks,
            dtype=np.int32,
        )

    def _score_tick_signal(
        self,
        peaks: np.ndarray,
    ) -> TickSignalScore:
        """
        Scores how strongly a set of candidate peaks resembles a ruler.

        The score considers:

            - number of candidate peaks
            - regularity of spacing between consecutive peaks

        More peaks are better, provided that their spacing is reasonably
        regular.

        Returns:
            A score where larger is better.
        """

        peak_count = len(peaks)

        # A ruler signal with fewer than three peaks gives us too little
        # information to meaningfully evaluate regularity.
        if peak_count < 3:
            return TickSignalScore(0.0, 0, 0.0)

        spacings = np.diff(peaks).astype(np.float32)

        if spacings.size == 0:
            return TickSignalScore(0.0, 0, 0.0)

        mean_spacing = float(
            np.mean(spacings)
        )

        if mean_spacing <= 0:
            return TickSignalScore(0.0, 0, 0.0)

        std_spacing = float(
            np.std(spacings)
        )

        # Coefficient of variation:
        #
        #     CV = standard deviation / mean
        #
        # This makes regularity independent of the absolute pixel scale.
        coefficient_of_variation = (
            std_spacing / mean_spacing
        )

        # Convert regularity into a score in [0, 1].
        #
        # CV = 0       -> perfect regularity
        # CV = 1       -> very irregular
        #
        # The exact transformation isn't critical yet. We mainly want
        # a smooth score rather than a hard cutoff.

        regularity_score = 1.0 / (
            1.0 + coefficient_of_variation
        )

        # Peak count should matter, but we don't want a signal with a
        # huge number of noisy peaks to automatically win.
        #
        # log1p gives diminishing returns:
        #
        # 3 -> useful
        # 10 -> better
        # 50 -> not 5x better
        #
        peak_count_score = np.log1p(
            peak_count
        )
        
        score=float(peak_count_score * regularity_score)
        
        return TickSignalScore(
            score=score,
            peak_count=peak_count,
            coefficient_of_variation=coefficient_of_variation
        )

    def _save_debug_image(
        self,
        rotated_ruler: RotatedRuler,
        signals: TickSignals,
        candidate_peaks: np.ndarray,
        selected_region: str,
        top_score,
        bottom_score,
        name: str | None,
    ) -> None:
        """
        Saves a visual debug representation of tick detection.

        The output contains:
            1. Rotated ruler image with ruler mask overlay.
            2. Top and bottom tick signals.
            3. Combined signal with the relative threshold.

        The x-axis of the signal plots corresponds directly to the
        horizontal pixel coordinate within the rotated ruler crop.
        """
        if name is None:
            name = "tick_detection"

        image = rotated_ruler.image
        mask = rotated_ruler.mask

        signal = signals.signal
        threshold = signals.threshold

        if image is None or image.size == 0:
            raise ValueError(
                "Cannot create tick debug image from empty ruler image."
            )

        if mask is None or mask.size == 0:
            raise ValueError(
                "Cannot create tick debug image from empty ruler mask."
            )

        if signal.size == 0:
            raise ValueError(
                "Cannot create tick debug image from empty tick signal."
            )

        # ---------------------------------------------------------
        # Prepare output directory
        # ---------------------------------------------------------

        debug_dir = Path(
            "test/analysis/measurement/debug"
        )

        debug_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = debug_dir / f"{name}_stage_3_tick_detection.png"

        # ---------------------------------------------------------
        # Prepare ruler visualization
        # ---------------------------------------------------------

        # Convert BGR -> RGB for matplotlib.
        rgb = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

        # Create a subtle mask overlay.
        #
        # We don't want to obscure the actual ruler image because
        # inspecting the relationship between ruler markings and
        # signal peaks is the whole purpose of this debug image.

        mask_binary = mask > 0

        overlay = rgb.copy()

        # Brighten pixels belonging to the detected ruler slightly.
        overlay[mask_binary] = (
            0.7 * overlay[mask_binary]
            + 0.3 * 255
        ).astype(np.uint8)

        # ---------------------------------------------------------
        # Create figure
        # ---------------------------------------------------------

        plt.style.use('dark_background')

        fig, axes = plt.subplots(
            3,
            1,
            figsize=(16, 10),
            gridspec_kw={
                "height_ratios": [2.5, 1.5, 2.0],
            },
        )

        # ---------------------------------------------------------
        # Panel 1: rotated ruler
        # ---------------------------------------------------------

        ax_image = axes[0]

        ax_image.imshow(overlay)

        ax_image.set_title(
            f"Rotated ruler / selected region: {selected_region}"
        )

        ax_image.set_xlim(
            0,
            image.shape[1] - 1,
        )

        ax_image.set_ylim(
            image.shape[0] - 1,
            0,
        )

        ax_image.set_ylabel("y [px]")

        # ---------------------------------------------------------
        # Panel 2: top and bottom signals
        # ---------------------------------------------------------

        ax_halves = axes[1]

        x = np.arange(len(signal))

        ax_halves.plot(
            x,
            signal,
            label="signal",
            linewidth=1.0,
        )

        ax_halves.set_title(
            "Normalized tick signals"
        )

        ax_halves.set_ylabel(
            "Signal strength"
        )

        ax_halves.set_ylim(
            0.0,
            1.05,
        )

        ax_halves.grid(
            True,
            alpha=0.25,
        )

        ax_halves.legend()

        # ---------------------------------------------------------
        # Panel 3: combined signal + threshold
        # ---------------------------------------------------------

        ax_signal = axes[2]
        ax_signal.text(
            0.0,
            -0.1,
            (
                f"selected: {selected_region} | "
                f"top score: {top_score:.3f} | "
                f"bottom score: {bottom_score:.3f} | "
                f"candidate peaks: {len(candidate_peaks)}"
            ),
            transform=ax_signal.transAxes,
            verticalalignment="top",
        )
        ax_signal.plot(
            x,
            signal,
            linewidth=1.5,
            label="selected signal",
        )

        ax_signal.axhline(
            threshold,
            linestyle="--",
            linewidth=1.2,
            label=f"threshold = {threshold:.3f}",
        )

        # Candidate tick positions.
        #
        # These are NOT final tick positions. They are simply the strongest
        # point inside each contiguous above-threshold region.

        if candidate_peaks.size > 0:
            candidate_values = signal[candidate_peaks]

            ax_signal.scatter(
                candidate_peaks,
                candidate_values,
                marker="o",
                s=30,
                zorder=5,
                label="candidate peaks",
            )

            for peak_x in candidate_peaks:
                ax_signal.axvline(
                    peak_x,
                    linestyle=":",
                    linewidth=0.7,
                    alpha=0.4,
                )

        # ---------------------------------------------------------
        # Mark threshold crossings
        # ---------------------------------------------------------

        above_threshold = signal >= threshold

        # Find contiguous regions where the signal exceeds the
        # threshold. These are deliberately called "candidate
        # regions", not ticks. Positioning will refine them later.

        transitions = np.diff(
            above_threshold.astype(np.int8)
        )

        starts = np.flatnonzero(
            transitions == 1
        ) + 1

        ends = np.flatnonzero(
            transitions == -1
        ) + 1

        if above_threshold[0]:
            starts = np.insert(
                starts,
                0,
                0,
            )

        if above_threshold[-1]:
            ends = np.append(
                ends,
                len(signal),
            )

        candidate_centers = []

        for start, end in zip(starts, ends):
            if end <= start:
                continue

            region = signal[start:end]

            peak_offset = int(
                np.argmax(region)
            )

            peak_x = start + peak_offset
            peak_y = signal[peak_x]

            candidate_centers.append(
                (peak_x, peak_y)
            )

        # Mark candidate peaks.
        #
        # Again: these are NOT final ticks. They are simply the
        # strongest locations inside above-threshold regions.

        if candidate_centers:
            candidate_x = np.array(
                [point[0] for point in candidate_centers]
            )

            candidate_y = np.array(
                [point[1] for point in candidate_centers]
            )

            ax_signal.scatter(
                candidate_x,
                candidate_y,
                marker="o",
                s=25,
                zorder=5,
                label="candidate peaks",
            )

            # Draw corresponding vertical guides.
            for candidate_x_value in candidate_x:
                ax_signal.axvline(
                    candidate_x_value,
                    linestyle=":",
                    linewidth=0.7,
                    alpha=0.4,
                )

        ax_signal.set_title(
            f"Selected {selected_region} third / candidate tick positions"
        )

        ax_signal.set_xlabel(
            "Horizontal position [px]"
        )

        ax_signal.set_ylabel(
            "Signal strength"
        )

        ax_signal.set_ylim(
            0.0,
            1.05,
        )

        ax_signal.grid(
            True,
            alpha=0.25,
        )

        ax_signal.legend()

        # ---------------------------------------------------------
        # Overall figure
        # ---------------------------------------------------------

        fig.suptitle(
            f"Tick detection: {name}",
            fontsize=14,
        )

        fig.tight_layout(
            rect=[0, 0, 1, 0.97],
        )

        fig.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(fig)