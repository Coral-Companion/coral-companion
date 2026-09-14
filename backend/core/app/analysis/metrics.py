from dataclasses import dataclass

import cv2
import numpy as np
from enum import Enum

class Metric(Enum):
    AREA_PIXELS = "Pixel Area"
    MEAN_L = "Mean LAB Lightness value [1-100]"
    MEDIAN_L = "Median LAB Lightness value [1-100]"
    STD_L = "Standard Deviation LAB Lightness [1-100]"
    P5_L = "5th Percentile LAB Lightness [1-100]"
    P10_L = "10th Percentile LAB Lightness [1-100]"
    P15_L = "15th Percentile LAB Lightness [1-100]"
    P25_L = "25th Percentile LAB Lightness [1-100]"
    P75_L = "75th Percentile LAB Lightness [1-100]"
    P85_L = "85th Percentile LAB Lightness [1-100]"
    P90_L = "90th Percentile LAB Lightness [1-100]"
    P95_L = "95th Percentile LAB Lightness [1-100]"
    DYNAMIC_RANGE_L = "Dynamic Range LAB Lightness [1-100]"
    MEAN_A = "Mean Red-Green Color Value [-127-127]"
    MEAN_B = "Mean Blue-Yellow Color Value [-127-127]"
    STD_A = "Red-Green Variation"
    STD_B = "Blue-Yellow Variation"
    SOBEL_MEAN = "Sobel Gradient Mean value"
    SOBEL_STD = "Sobel Gradient Standard Deviation"
    SOBEL_MEDIAN = "Sobel Gradient Median"
    SOBEL_P95 = "Sobel 95th Percentile"
    LAPLACIAN_VARIANCE = "Laplacian Variable"


def coral_mask(image: np.ndarray) -> np.ndarray:
    """
    Returns True for every non-black coral pixel.
    """
    if image.shape[2] == 4:
        return image[:, :, 3] > 0

    return np.any(image != 0, axis=2)

def lab_image(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image[:, :, :3], cv2.COLOR_RGB2LAB)


def valid_pixels(channel: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return channel[mask]


def brightness_metrics(image: np.ndarray) -> dict:
    mask = coral_mask(image)

    L = lab_image(image)[:, :, 0].astype(np.float32)
    L *= 100 / 255
    pixels = valid_pixels(L, mask)

    metrics = {
        Metric.MEAN_L.name: float(np.mean(pixels)),
        Metric.MEDIAN_L.name: float(np.median(pixels)),
        Metric.STD_L.name: float(np.std(pixels)),
    }

    for p in [5, 10, 15, 25, 75, 85, 90, 95]:
        metrics[Metric[f"P{p}_L"].name] = float(np.percentile(pixels, p))

    metrics[Metric.DYNAMIC_RANGE_L.name] = (
        metrics[Metric.P95_L.name] - metrics[Metric.P5_L.name]
    )

    return metrics


def brightness_histogram(
    image: np.ndarray,
    bins: int = 50,
):

    mask = coral_mask(image)

    L = lab_image(image)[:, :, 0].astype(np.float32)
    L *= 100 / 255
    
    pixels = valid_pixels(L, mask)

    hist, edges = np.histogram(
        pixels,
        bins=bins,
        range=(0, 100),
        density=True,
        
    )
    return hist, edges


def color_metrics(image: np.ndarray):
    lab = lab_image(image).astype(np.float32)
    
    A = lab[:, :, 1].astype(np.float32) - 128
    B = lab[:, :, 2].astype(np.float32) - 128

    return {
        Metric.MEAN_A.name: float(np.mean(A)),
        Metric.MEAN_B.name: float(np.mean(B)),
        Metric.STD_A.name: float(np.std(A)),
        Metric.STD_B.name: float(np.std(B)),
    }


def sobel_image(image: np.ndarray):
    mask = coral_mask(image)
    
    L = lab_image(image)[:, :, 0].astype(np.float32)
    L *= 100 / 255
    
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    magnitude *= mask.astype(np.float32)
    return magnitude


def sobel_metrics(image):

    sobel = sobel_image(image)

    pixels = sobel[sobel > 0]

    return {
        Metric.SOBEL_MEAN.name: float(np.mean(pixels)),
        Metric.SOBEL_STD.name: float(np.std(pixels)),
        Metric.SOBEL_MEDIAN.name: float(np.median(pixels)),
        Metric.SOBEL_P95.name: float(np.percentile(pixels, 95)),
    }


def laplacian_image(image):
    mask = coral_mask(image)

    L = lab_image(image)[:, :, 0].astype(np.float32)
    L *= 100 / 255
    
    lap = cv2.Laplacian(L, cv2.CV_32F, ksize=3)
    lap *= mask.astype(np.float32)

    return lap


def laplacian_metrics(image):
    lap = laplacian_image(image)

    pixels = lap[lap != 0]

    return {
        Metric.LAPLACIAN_VARIANCE.name: float(np.var(pixels))
    }


def shape_metrics(image):
    mask = coral_mask(image)

    return {
        Metric.AREA_PIXELS.name: int(np.count_nonzero(mask))
    }



def compute_metrics(image):

    metrics = {
        "Shape": {},
        "Brightness": {},
        "Color": {},
        "Texture": {}
    }

    metrics["Brightness"].update(
        brightness_metrics(image)
    )

    metrics["Color"].update(
        color_metrics(image)
    )

    metrics["Texture"].update(
        sobel_metrics(image)
    )

    metrics["Texture"].update(
        laplacian_metrics(image)
    )

    metrics["Shape"].update(
        shape_metrics(image)
    )

    return metrics