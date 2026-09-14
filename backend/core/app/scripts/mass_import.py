"""
Mass-import coral observations from a dated image directory.

Expected directory name:
    YYYYMMDD

Example:
    20260711/

Expected image filenames:
    CR_olohuita_T01_c001.JPG
    CR_IslaLarga_T01_c013_A.JPG

Filename interpretation:
    CR_<dive_site>_<transect>_<coral_name>[...].JPG

Examples:
    CR_olohuita_T01_c001.JPG
        Dive site: Olohuita
        Coral name: c001

    CR_IslaLarga_T01_c013_A.JPG
        Dive site: Isla Larga
        Coral name: c013

Images that do not match the expected filename pattern are ignored.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import cv2
from dotenv import load_dotenv
import os

load_dotenv()

from app.orchestration.coral_service import CoralService
from app.persistence.monitoring_session_repository import (
    MonitoringSessionRepository,
)
from app.domain.monitoring_session import MonitoringSession


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

IMAGE_PATTERN = re.compile(
    r"^CR_"
    r"(?P<dive_site>[^_]+)"
    r"_"
    r"(?P<transect>[^_]+)"
    r"_"
    r"(?P<coral_name>c\d+)"
    r"(?:_[^_]+)*"
    r"\.(?:jpg|jpeg|JPG|JPEG)$",
)


@dataclass(frozen=True)
class ImageImport:
    path: Path
    dive_site: str
    coral_name: str


def format_dive_site(raw_dive_site: str) -> str:
    """
    Convert the compact filename representation into the DB dive-site name.

    Examples:
        olohuita   -> Olohuita
        IslaLarga  -> Isla Larga
        islaLarga  -> Isla Larga
    """

    # Insert a space before an uppercase letter when it follows a lowercase
    # letter:
    #
    # IslaLarga -> Isla Larga
    #
    formatted = re.sub(
        r"(?<=[a-z])(?=[A-Z])",
        " ",
        raw_dive_site,
    )

    return formatted.capitalize()


def parse_image_filename(path: Path) -> ImageImport | None:
    """
    Parse a filename into the dive site and coral name.

    Returns None for filenames that do not match the expected format.
    """

    match = IMAGE_PATTERN.match(path.name)

    if match is None:
        return None

    dive_site = format_dive_site(
        match.group("dive_site")
    )

    coral_name = match.group("coral_name")

    return ImageImport(
        path=path,
        dive_site=dive_site,
        coral_name=coral_name,
    )


# ---------------------------------------------------------------------------
# Monitoring session matching
# ---------------------------------------------------------------------------

def get_session_dive_site(session) -> str:
    return session.dive_site


def find_monitoring_session(
    sessions: list[MonitoringSession],
    dive_site: str,
    monitoring_date 
):
    """
    Find the monitoring session belonging to the dive site.

    A monitoring session is assumed to belong to exactly one dive site.
    """

    matching_sessions = [ 
        session
        for session in sessions 
        if (
                get_session_dive_site(session).casefold() == dive_site.casefold()
                and session.timestamp.date() == monitoring_date 
        ) 
    ]

    if not matching_sessions:
        raise ValueError(
            f"No monitoring session found for dive site "
            f"'{dive_site}'."
        )

    if len(matching_sessions) > 1:
        raise ValueError(
            f"Multiple monitoring sessions found for dive site "
            f"'{dive_site}'. "
            f"The import cannot safely determine which one to use."
        )

    return matching_sessions[0]


# ---------------------------------------------------------------------------
# Image handling
# ---------------------------------------------------------------------------

def load_image(path: Path):
    """
    Load an image using OpenCV.

    OpenCV loads images as BGR, which is the format expected by the existing
    CoralService pipeline.
    """

    image = cv2.imread(
        str(path),
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise ValueError(
            f"Could not read image: {path}"
        )

    return image


# ---------------------------------------------------------------------------
# Import process
# ---------------------------------------------------------------------------

def import_directory(
    directory: Path,
    monitoring_session_repository: MonitoringSessionRepository,
    coral_service: CoralService,
) -> None:

    print("=" * 80)
    print("CORAL MASS IMPORT")
    print("=" * 80)
    print(f"Directory: {directory}")
    print()

    # ------------------------------------------------------------------
    # Validate directory name
    # ------------------------------------------------------------------

    monitoring_date = {}
    try:
        monitoring_date = datetime.strptime(
            directory.name,
            "%Y%m%d",
        ).date()
        
    except ValueError:
        raise ValueError(
            f"Directory name must be formatted as YYYYMMDD. "
            f"Received: '{directory.name}'."
        )

    print(
        f"Monitoring date: "
        f"{monitoring_date.isoformat()}"
    )

    # ------------------------------------------------------------------
    # Load all existing monitoring sessions
    # ------------------------------------------------------------------

    print()
    print("Loading monitoring sessions...")

    sessions = monitoring_session_repository.find_all()

    print(
        f"Loaded {len(sessions)} monitoring session(s)."
    )

    # ------------------------------------------------------------------
    # Parse filenames
    # ------------------------------------------------------------------

    imports: list[ImageImport] = []
    ignored_files: list[Path] = []

    for path in sorted(directory.iterdir()):

        if not path.is_file():
            continue

        parsed = parse_image_filename(path)

        if parsed is None:
            ignored_files.append(path)
            continue

        imports.append(parsed)

    print()
    print(
        f"Found {len(imports)} importable image(s)."
    )

    if ignored_files:
        print(
            f"Ignoring {len(ignored_files)} file(s) "
            f"with unsupported filenames."
        )

    if not imports:
        print()
        print("Nothing to import.")
        return

    # ------------------------------------------------------------------
    # Resolve monitoring sessions before processing images
    # ------------------------------------------------------------------

    print()
    print("Resolving monitoring sessions by dive site...")

    sessions_by_dive_site = {}

    for image_import in imports:

        dive_site_key = image_import.dive_site.casefold()

        if dive_site_key in sessions_by_dive_site:
            continue

        print(f"finding monitoring session for {image_import.coral_name}")
        session = find_monitoring_session(
            sessions=sessions,
            dive_site=image_import.dive_site,
            monitoring_date=monitoring_date,
        )

        sessions_by_dive_site[dive_site_key] = session

        print(
            f"  {image_import.dive_site} -> "
            f"monitoring session {session.id}"
        )

    # ------------------------------------------------------------------
    # Process images
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("STARTING IMPORT")
    print("=" * 80)
    print()

    total = len(imports)
    processed = 0
    successful = 0
    failed = 0

    start_time = time.perf_counter()

    for image_import in imports:

        processed += 1
        remaining = total - processed

        session = sessions_by_dive_site[
            image_import.dive_site.casefold()
        ]

        print(
            f"[{processed}/{total}] "
            f"Processing: {image_import.path.name}"
        )

        print(
            f"  {remaining} image(s) left"
        )

        print(
            f"  Dive site: {image_import.dive_site}"
        )

        print(
            f"  Coral: {image_import.coral_name}"
        )

        print(
            f"  Monitoring session: {session.id}"
        )

        try:

            # ----------------------------------------------------------
            # Load image
            # ----------------------------------------------------------

            image = load_image(
                image_import.path
            )

            print(
                f"  Image size: "
                f"{image.shape[1]}x{image.shape[0]}"
            )

            # ----------------------------------------------------------
            # Segment image
            # ----------------------------------------------------------

            print(
                "  Segmenting image..."
            )

            segmentation_result = (
                coral_service.segment_image(
                    image=image,
                    filename=image_import.path.name,
                )
            )

            segments = segmentation_result.segments

            print(
                f"  Found {len(segments)} segment(s)"
            )

            if not segments:
                print(
                    "  WARNING: No segments found. "
                    "Skipping observation."
                )

                failed += 1
                continue

            # ----------------------------------------------------------
            # Confirm observation
            # ----------------------------------------------------------

            print(
                "  Saving observation..."
            )

            result = coral_service.confirm_observation(
                image=image,
                segments=segments,
                dive_site=image_import.dive_site,
                coral_name=image_import.coral_name,
                monitoring_session_id=str(
                    session.id
                ),
            )

            successful += 1

            print(
                f"  SUCCESS: Observation saved with id {result.observation.id} "
            )

            # If your ConfirmResult exposes an observation ID,
            # this can be uncommented/adapted:
            #
            # print(f"  Observation ID: {result.observation.id}")

        except Exception as exc:

            failed += 1

            print(
                f"  ERROR: {type(exc).__name__}: {exc}"
            )

            # Continue processing the remaining images rather than
            # terminating the entire import.
            continue

        print()

    elapsed = time.perf_counter() - start_time

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)

    print(
        f"Total images:       {total}"
    )

    print(
        f"Successfully saved:  {successful}"
    )

    print(
        f"Failed:              {failed}"
    )

    print(
        f"Elapsed time:        {elapsed:.1f}s"
    )

    if successful:
        print(
            f"Average per success: "
            f"{elapsed / successful:.1f}s"
        )

    print("=" * 80)


# ---------------------------------------------------------------------------
# Dependency construction
# ---------------------------------------------------------------------------

def create_services():
    """
    Construct the application's repositories and services.

    Replace this section with your project's existing dependency wiring if
    CoralService requires additional constructor dependencies.
    """

    monitoring_session_repository = (
        MonitoringSessionRepository()
    )

    coral_service = CoralService()

    return (
        monitoring_session_repository,
        coral_service,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Mass-import coral observations from a YYYYMMDD "
            "image directory."
        )
    )

    parser.add_argument(
        "directory",
        type=Path,
        help=(
            "Directory containing the images. "
            "The directory name must be formatted as YYYYMMDD."
        ),
    )

    args = parser.parse_args()

    directory = args.directory.resolve()

    if not directory.exists():
        print(
            f"ERROR: Directory does not exist: {directory}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not directory.is_dir():
        print(
            f"ERROR: Path is not a directory: {directory}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:

        (
            monitoring_session_repository,
            coral_service,
        ) = create_services()

        import_directory(
            directory=directory,
            monitoring_session_repository=(
                monitoring_session_repository
            ),
            coral_service=coral_service,
        )

    except Exception as exc:

        print(
            f"\nFATAL ERROR: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

        sys.exit(1)


if __name__ == "__main__":
    main()

