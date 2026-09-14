import argparse
from pathlib import Path

import cv2

from app.orchestration.coral_service import CoralService
from app.vision.vision_service import VisionService

def process_directory(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    coral_service = CoralService()

    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    image_files = sorted(
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    )

    print(f"Found {len(image_files)} images.")

    for image_file in image_files:
        print(f"\nProcessing {image_file.name}")

        image = cv2.imread(str(image_file))

        if image is None:
            print("  Could not read image.")
            continue

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        try:
            segmentation = coral_service.segment_image(image=image, filename=image_file.name)

            if not segmentation.segments:
                print("  No coral segments found, skipping to next image.")
                continue

            print(f"Found {len(segmentation.segments)} segment(s). Creating separate crops for each.")

            for index, segment in enumerate(segmentation.segments):
                identify_result = coral_service.identify(image=image, segments=[segment])

                cropped = identify_result.crop
                image_path = Path(image_file.name)
                output_path = output_dir / f"{image_path.stem}-crop-{index+1}.png"
                cropped_bgr = cv2.cvtColor(cropped, cv2.COLOR_RGBA2BGRA)
                cv2.imwrite(str(output_path), cropped_bgr)

                print(f"  Saved {output_path.name}")

        except Exception as ex:
            print(f"  ERROR: {ex}")


def main():
    parser = argparse.ArgumentParser(description="Crop corals from all images in a directory.")
    parser.add_argument("input_directory", type=Path, help="Directory containing original images")
    parser.add_argument("output_directory", type=Path, help="Directory to write cropped images")
    args = parser.parse_args()
    process_directory(args.input_directory, args.output_directory,)


if __name__ == "__main__":
    main()