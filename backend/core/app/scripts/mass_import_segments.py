from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from app.persistence.database import engine
from app.domain.observation import Observation


def parse_fixture_datetime(filename: str) -> datetime:
    """
    Parse fixture filename:

        20260724_2021.json

    into:

        2026-07-24 20:21
    """

    timestamp = Path(filename).stem

    try:
        return datetime.strptime(
            timestamp,
            "%Y%m%d_%H%M",
        )

    except ValueError as exc:
        raise ValueError(
            f"Fixture filename '{filename}' does not match "
            f"expected format YYYYMMDD_HHMM.json"
        ) from exc


def get_coral_name_from_directory(directory_name: str) -> str:
    """
    Extract coral name from fixture directory name.

    Example:

        islalarga_c003 -> c003
    """

    parts = directory_name.rsplit("_", 1)

    if len(parts) != 2:
        raise ValueError(
            f"Fixture directory '{directory_name}' does not match "
            f"expected format '<dive_site>_<coral_name>'."
        )

    return parts[1].casefold()


def find_observation(
    session: Session,
    coral_name: str,
    fixture_datetime: datetime,
) -> Observation | None:
    """
    Find the observation belonging to a fixture.

    Matching criteria:

    - coral name
    - date of creation
    - hour of creation
    - minute of creation

    Seconds and microseconds are intentionally ignored because the fixture
    filename only contains precision down to the minute.
    """

    observations = session.exec(
        select(Observation)
        .where(
            Observation.coral_name.ilike(coral_name),
            Observation.created_at >= fixture_datetime,
            Observation.created_at
            < fixture_datetime.replace(
                second=0,
                microsecond=0,
            ).replace(
                minute=fixture_datetime.minute + 1
            )
        )
    ).all()

    if not observations:
        return None

    if len(observations) > 1:
        raise ValueError(
            f"Multiple observations found for "
            f"'{coral_name}' at "
            f"{fixture_datetime.strftime('%Y-%m-%d %H:%M')}."
        )

    return observations[0]


def load_fixture_segments(
    fixture_path: Path,
) -> list[dict]:
    """
    Load and return segments from a CoralSCOP fixture JSON.
    """

    with fixture_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        fixture = json.load(file)

    segments = fixture.get("segments")

    if not isinstance(segments, list):
        raise ValueError(
            f"Fixture '{fixture_path}' does not contain "
            f"a valid 'segments' list."
        )

    return segments


def collect_fixture_files(
    fixtures_directory: Path,
) -> list[Path]:
    """
    Recursively collect all fixture JSON files.

    Ignores:

    - default.json
    - files that do not follow YYYYMMDD_HHMM.json
    """

    fixture_files = []

    for path in sorted(
        fixtures_directory.rglob("*.json")
    ):
        if path.name == "default.json":
            continue

        try:
            parse_fixture_datetime(path.name)
        except ValueError:
            print(
                f"Skipping unsupported fixture filename: "
                f"{path}"
            )
            continue

        fixture_files.append(path)

    return fixture_files


def import_segments(
    fixtures_directory: Path,
) -> None:

    print("=" * 80)
    print("IMPORT FIXTURE SEGMENTS")
    print("=" * 80)
    print(
        f"Directory: {fixtures_directory.resolve()}"
    )
    print()

    fixture_files = collect_fixture_files(
        fixtures_directory
    )

    print(
        f"Found {len(fixture_files)} fixture file(s)."
    )
    print()

    if not fixture_files:
        print("Nothing to import.")
        return

    updated = 0
    skipped = 0
    failed = 0

    with Session(engine) as session:

        for index, fixture_path in enumerate(
            fixture_files,
            start=1,
        ):

            print(
                f"[{index}/{len(fixture_files)}] "
                f"{fixture_path}"
            )

            try:

                coral_name = (
                    get_coral_name_from_directory(
                        fixture_path.parent.name
                    )
                )

                fixture_datetime = (
                    parse_fixture_datetime(
                        fixture_path.name
                    )
                )

                segments = load_fixture_segments(
                    fixture_path
                )

                observation = find_observation(
                    session=session,
                    coral_name=coral_name,
                    fixture_datetime=fixture_datetime,
                )

                if observation is None:
                    print(
                        "  SKIPPED: no matching observation found"
                    )
                    skipped += 1
                    continue

                if observation.segments is not None:
                    print(
                        "  WARNING: observation already has "
                        "segments — overwriting"
                    )

                observation.segments = segments

                session.add(observation)
                session.commit()

                print(
                    f"  UPDATED observation "
                    f"{observation.id}"
                )

                print(
                    f"  Segments: {len(segments)}"
                )

                updated += 1

            except Exception as exc:

                session.rollback()

                print(
                    f"  FAILED: "
                    f"{type(exc).__name__}: {exc}"
                )

                failed += 1

    print()
    print("=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")
    print("=" * 80)


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Import CoralSCOP segments from dev fixtures "
            "into existing observations."
        )
    )

    parser.add_argument(
        "--fixtures_dir",
        required=True,
        type=Path,
        help=(
            "Root directory containing fixture directories, "
            "for example: dev_fixtures/"
        ),
    )

    args = parser.parse_args()

    if not args.fixtures_dir.exists():
        raise ValueError(
            f"Fixture directory does not exist: "
            f"{args.fixtures_dir}"
        )

    if not args.fixtures_dir.is_dir():
        raise ValueError(
            f"Fixture path is not a directory: "
            f"{args.fixtures_dir}"
        )

    import_segments(
        args.fixtures_dir
    )


if __name__ == "__main__":

    try:
        main()

    except Exception as exc:

        print()
        print(
            f"FATAL ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        sys.exit(1)