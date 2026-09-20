from pathlib import Path

import cv2
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

from .metrics import (
    brightness_histogram,
    coral_mask,
    lab_image,
    laplacian_image,
    sobel_image,
)


def _save(fig: Figure, filename: Path):
    fig.tight_layout()
    fig.savefig(filename,
                dpi=200,
                bbox_inches="tight",
                facecolor=fig.get_facecolor(),
                edgecolor=fig.get_facecolor(),)
    plt.close(fig)

def style_dark_figure(fig, axes):
    fig.patch.set_facecolor("#071116")

    # Normalize axes input
    if isinstance(axes, np.ndarray):
        axes_list = axes.flatten().tolist()

    elif isinstance(axes, (list, tuple)):
        axes_list = list(axes)

    else:
        axes_list = [axes]

    for ax in axes_list:
        ax.set_facecolor("#071116")

        # Axis text
        ax.tick_params(
            colors="#94a3b8",
            which="both"
        )

        # Axis labels
        ax.xaxis.label.set_color("#cbd5e1")
        ax.yaxis.label.set_color("#cbd5e1")

        # Title
        ax.title.set_color("#f1f5f9")

        # Spines
        for spine in ax.spines.values():
            spine.set_color("#334155")

        # Grid
        ax.grid(
            True,
            color="#334155",
            alpha=0.3
        )

def style_colorbar(cbar):
    cbar.ax.set_facecolor("#071116")

    cbar.ax.tick_params(
        colors="#cbd5e1"
    )

    cbar.outline.set_edgecolor("#334155")

    for label in cbar.ax.get_yticklabels():
        label.set_color("#cbd5e1")
    cbar.ax.xaxis.label.set_color("#cbd5e1")
    cbar.ax.yaxis.label.set_color("#cbd5e1")

def save_original(image: np.ndarray, filename: Path):
    fig, ax = plt.subplots(figsize=(6, 6))

    style_dark_figure(fig, ax)
    
    ax.imshow(image)
    ax.axis("off")

    _save(fig, filename)

def save_histogram(
    image_a: np.ndarray,
    image_b: np.ndarray,
    filename: Path,
):

    hist_a, edges = brightness_histogram(image_a)
    hist_b, _ = brightness_histogram(image_b)

    centres = (edges[:-1] + edges[1:]) / 2

    fig, ax = plt.subplots(figsize=(8, 4), 
    facecolor="#071116")
    
    style_dark_figure(fig, ax)

    ax.plot(centres, hist_a, label="First Coral")
    ax.plot(centres, hist_b, label="Second Coral")

    ax.set_xlabel("Lightness (L)")
    ax.set_ylabel("Relative frequency")

    ax.legend()

    _save(fig, filename)


def save_lab_scatter(
    image_a: np.ndarray,
    image_b: np.ndarray,
    filename: Path,
    sample_size: int = 20_000,
):

    rng = np.random.default_rng(42)

    lab_a = lab_image(image_a)
    lab_b = lab_image(image_b)

    mask_a = coral_mask(image_a)
    mask_b = coral_mask(image_b)

    a_a = lab_a[:, :, 1][mask_a]
    b_a = lab_a[:, :, 2][mask_a]

    a_b = lab_b[:, :, 1][mask_b]
    b_b = lab_b[:, :, 2][mask_b]

    if len(a_a) > sample_size:
        idx = rng.choice(len(a_a), sample_size, replace=False)
        a_a = a_a[idx]
        b_a = b_a[idx]

    if len(a_b) > sample_size:
        idx = rng.choice(len(a_b), sample_size, replace=False)
        a_b = a_b[idx]
        b_b = b_b[idx]

    fig, ax = plt.subplots(figsize=(6, 6), 
    facecolor="#071116")
    
    style_dark_figure(fig, ax)

    ax.scatter(
        a_a,
        b_a,
        s=3,
        alpha=0.25,
        label="First Coral",
    )

    ax.scatter(
        a_b,
        b_b,
        s=3,
        alpha=0.25,
        label="Second Coral",
    )

    ax.set_xlabel("a (green ↔ red)")
    ax.set_ylabel("b (blue ↔ yellow)")
    ax.set_title("Lab Colour Distribution")

    ax.legend()

    _save(fig, filename)

def sobel(image: np.ndarray) -> Figure:

    sobel = sobel_image(image)

    pixels = sobel[sobel > 0]

    if len(pixels) == 0:
        vmax = 1
    else:
# TODO: potentially control this as env var
        vmax= 60

    fig, ax = plt.subplots(figsize=(6, 6), 
    facecolor="#071116")
    
    style_dark_figure(fig, ax)

    im = ax.imshow(
        sobel,
        cmap="cividis",
        vmin=0,
        vmax=vmax,
    )

    ax.axis("off")

    cbar = fig.colorbar(
        im,
        ax=ax,
        shrink=0.8,
        label="Gradient magnitude",
    )
    
    style_colorbar(cbar)

    return fig


def laplacian(image: np.ndarray) -> Figure:

    lap = laplacian_image(image)

    pixels = np.abs(lap[lap != 0])

    if len(pixels) == 0:
        vmax = 1
    else:
        vmax = np.percentile(pixels, 99)
        vmax = 40

    fig, ax = plt.subplots(figsize=(6, 6), 
    facecolor="#071116")
    
    style_dark_figure(fig, ax)

    im = ax.imshow(
        lap,
        cmap="twilight",
        vmin=-vmax,
        vmax=vmax,
    )

    ax.set_title("Laplacian Response")
    ax.axis("off")

    cbar = fig.colorbar(
        im,
        ax=ax,
        shrink=0.8,
        label="Second derivative",
    )
    
    style_colorbar(cbar)

    return fig


def save_brightness_difference(
    image_a: np.ndarray,
    image_b: np.ndarray,
    filename: Path,
):
    COMPARE_SIZE = (512, 512)

    lab_a_image = lab_image(image_a)[:, :, 0].astype(np.float32)
    lab_a_image *= 100 / 255
    lab_a = cv2.resize(
        lab_a_image,
        COMPARE_SIZE,
        interpolation=cv2.INTER_AREA,
    )

    lab_b_image = lab_image(image_b)[:, :, 0].astype(np.float32)
    lab_b_image *= 100 / 255
    lab_b = cv2.resize(
        lab_b_image,
        COMPARE_SIZE,
        interpolation=cv2.INTER_AREA,
    )

    mask_a = cv2.resize(
        coral_mask(image_a).astype(np.uint8),
        COMPARE_SIZE,
        interpolation=cv2.INTER_NEAREST,
    ).astype(bool)

    mask_b = cv2.resize(
        coral_mask(image_b).astype(np.uint8),
        COMPARE_SIZE,
        interpolation=cv2.INTER_NEAREST,
    ).astype(bool)

    mask = mask_a & mask_b

    diff = np.zeros_like(lab_a)

    diff[mask] = lab_b[mask] - lab_a[mask]
    vmax = np.percentile(np.abs(diff[mask]), 99)

    diff_display = np.ma.masked_where(~mask, diff)

    fig, ax = plt.subplots(figsize=(6, 6), 
    facecolor="#071116")

    im = ax.imshow(
        diff_display,
        cmap="twilight",
        vmin=-vmax,
        vmax=vmax,
    )
    
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, label="Brightness Difference")
    
    style_colorbar(cbar)
    style_dark_figure(fig, ax)

    ax.axis("off")
    
    _save(fig, filename)

def save_texture_difference(
    image_a: np.ndarray,
    image_b: np.ndarray,
    filename: Path,
):

    sobel_a = sobel_image(image_a)
    sobel_b = sobel_image(image_b)

    mask = coral_mask(image_a) & coral_mask(image_b)

    diff = np.zeros_like(sobel_a)

    diff[mask] = sobel_b[mask] - sobel_a[mask]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10,5)
    )
    
    vmax = max(
        np.percentile(sobel_a, 99),
        np.percentile(sobel_b, 99)
    )

    im = axes[0].imshow(
        sobel_a,
        cmap="inferno",
        vmin=0,
        vmax=vmax
    )

    axes[1].imshow(
        sobel_b,
        cmap="inferno",
        vmin=0,
        vmax=vmax
    )

    fig.colorbar(
        im,
        ax=axes,
        fraction=0.046,
        pad=0.04,
        label="Sobel gradient magnitude"
    )
    style_dark_figure(fig, axes)

    
    vmin = 0
    
    axes.imshow(
        sobel_a,
        cmap="RdBu_r",
        vmin=vmin,
        vmax=vmax
    )
    
    axes.imshow(
        sobel_b,
        cmap="RdBu_r",
        vmin=vmin,
        vmax=vmax
    )
    
    #axes.imshow(
    #    diff,
    #    cmap="RdBu_r",
    #    vmin=-vmax,
    #    vmax=vmax,
    #)

    axes.axis("off")

    _save(fig, filename)


def save_side_by_side(
    image_a: np.ndarray,
    image_b: np.ndarray,
    filename: Path,
):

    fig, ax = plt.subplots(1, 2, figsize=(10, 5), 
    facecolor="#071116")
    
    style_dark_figure(fig, ax)

    ax[0].imshow(image_a)
    ax[0].set_title("Image A")
    ax[0].axis("off")

    ax[1].imshow(image_b)
    ax[1].set_title("Image B")
    ax[1].axis("off")

    _save(fig, filename)


def generate_all_figures(
    image_a: np.ndarray,
    image_b: np.ndarray,
    output_dir: Path,
):

    output_dir.mkdir(parents=True, exist_ok=True)

    save_side_by_side(
        image_a,
        image_b,
        output_dir / "images.png",
    )

    save_histogram(
        image_a,
        image_b,
        output_dir / "brightness_histogram.png",
    )

    save_lab_scatter(
        image_a,
        image_b,
        output_dir / "lab_scatter.png",
    )

    sobel(
        image_a,
    )

    sobel(
        image_b,
    )

    laplacian(
        image_a,
    )

    laplacian(
        image_b,
    )

    save_brightness_difference(
        image_a,
        image_b,
        output_dir / "brightness_difference.png",
    )

    #save_texture_difference(
    #    image_a,
    #    image_b,
    #    output_dir / "texture_difference.png",
    #)