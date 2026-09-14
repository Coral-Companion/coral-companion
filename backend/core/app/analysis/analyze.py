from pathlib import Path
import argparse
import cv2
import numpy as np

from .visualization import generate_all_figures
from .report import create_report

def load_image(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Load an image and create a foreground mask.

    Returns:
        image : RGB or RGBA image
        mask  : H x W bool (True = coral pixels)
    """

    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)

    if image is None:
        raise FileNotFoundError(path)

    if image.ndim != 3:
        raise ValueError(f"Expected color image: {path}")

    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        mask = image[:, :, 3] > 0

    elif image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = np.any(image != 0, axis=2)

    else:
        raise ValueError(f"Unsupported image format ({image.shape[2]} channels): {path}")

    if not np.any(mask):
        raise ValueError(f"No foreground pixels found in {path}")

    return image, mask

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("output")

    args = parser.parse_args()

    image_before, mask_before = load_image(args.before)
    image_after, mask_after = load_image(args.after)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_all_figures(
        image_before,
        image_after,
        output_dir,
    )

    create_report(
        image_before,
        image_after,
        output_dir,
    )

    print()
    print("Analysis complete.")
    print(f"Report written to {output_dir / 'report.html'}")


if __name__ == "__main__":
    main()