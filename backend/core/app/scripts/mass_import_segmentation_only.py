import argparse
from pathlib import Path
import cv2

from app.segmentation.coralscop_provider import CoralScopProvider

def process_directory(input_dir: Path):
    """
    Creates a dev fixture for all jpg images in the input_dir. 
    Only orchestrates and lets the coralscop provider trigger the actual fixture creation.
    """

    segmenter = CoralScopProvider()

    supported_extensions = {
        ".jpg",
        ".jpeg",
    }

    image_files = sorted(
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    )

    print(f"Found {len(image_files)} images.")

    for image_file in image_files:
        print(f"\nProcessing {image_file.name}")

        image = cv2.imread(str(image_file), cv2.IMREAD_COLOR)

        if image is None:
            print("  Could not read image.")
            continue

        #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        segmenter.segment(image=image, image_filename=image_file.name)


def main():
    parser = argparse.ArgumentParser(description="Segment corals from all images in a directory into dev fixtures.")
    parser.add_argument("input_directory", type=Path, help="Directory containing original images")
    args = parser.parse_args()
    process_directory(args.input_directory)


if __name__ == "__main__":
    main()