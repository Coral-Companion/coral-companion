import pytest
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

from app.analysis.measurement.coral_measurement_service import CoralMeasurementService
from app.analysis.measurement.models import CoralMeasurement
from app.segmentation.fixture_provider import FixtureProvider
from app.segmentation.coralscop_provider import CoralScopProvider

import app.utils.fixtures as fixtures

FIXTURES_DIR = Path("dev_fixtures")
PX_PER_CM_ERROR_TOLERANCE_RATIO=0.05
FERET_ERROR_TOLERANCE=0.5

measurement_service = CoralMeasurementService()
fixture_segmenter = FixtureProvider()

def run_measurement_for(coral_name: str, instance_name: str, target_segment_index: int = 0):
    instance_image_filename = f"{instance_name}.jpg"
    
    path = fixtures.get_fixture_image_path(coral_name, instance_image_filename)
    image = cv2.imread(str(path))
    
    segments = fixtures.get_segments(coral_name, f"{instance_name}.json")
    segment = segments[target_segment_index]
    
    measurement = measurement_service.measure_coral(image, segment, instance_name)
    return measurement


def test_measure_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    instance_name = "20260819_1813"
    target_segment_index = 0
    measurement = run_measurement_for(coral_name, instance_name, target_segment_index)
    
    # 1-2: 190px, 2-3: 185, 3-4: 188, 4-5: 186, 5-6: 195, 6-7: 192, 7-8: 202, 8-9: 200
    assert_results(measurement, expected_px_per_cm=192, expected_feret=6.9)


def test_measure_algalpavona():
    coral_name = "unknown_algalpavona"
    instance_name = "20260821_1341"
    
    measurement = run_measurement_for(coral_name, instance_name)
    
    # 0-1cm: 240px, 1-2cm: 235px, 2-3cm: 230px, 5-6cm: 237px, 6-7cm: 239px, 7-8cm: 249
    assert_results(measurement, 238, 4.7)


def test_measure_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    instance_name = "20260809_2059"
    
    measurement = run_measurement_for(coral_name, instance_name)
    
    # 1-2cm: 194px, 2-3cm: 195px, 3-4cm: 190px, 4-5cm: 191px, 5-6cm: 189px, 6-7cm: 192px
    assert_results(measurement, 191, 9.6)


def test_measure_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    instance_name = "20260824_1426_branchypavona_hd"

    measurement = run_measurement_for(coral_name, instance_name)

    # 0-1cm: 198, 1-2cm: 194, 2-3cm: 188, 3-4cm: 184, 4-5cm: 184, 5-6cm: 182, 6-7cm: 185
    assert_results(measurement, 187, 6.45)


def test_measure_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    instance_name = "20260821_1605_hd"

    with pytest.raises(ValueError, match="Could not find a sufficiently large cluster of regularly spaced ticks"):
        measurement = run_measurement_for(coral_name, instance_name)
        # 0-1cm: 273px, 1-2cm: , 2-3cm: , 3-4cm: , 4-5cm: , 5-6cm: , 6-7cm: 
        #assert_results(measurement, 273, 8.8)


def test_dark_pocillopora_low_definition():
    coral_name = "unknown_darkpocillopora"
    instance_name = "20260811_1639_darkpocillopora"

    measurement = run_measurement_for(coral_name, instance_name)

    # 0-1: 54, 1-2: 52, 2-3: 53, 3-4: 53, 4-5: 56, 5-6: 60, 6-7: 65
    assert_results(measurement, 56, 8.8)


def test_dark_pocillopora_high_definition():
    coral_name = "unknown_darkpocillopora"
    instance_name = "20260811_1639_darkpocillopora_hd"

    measurement = run_measurement_for(coral_name, instance_name)

    # 0-1: 255, 1-2: 260, 2-3: 262, 3-4: 268, 4-5: 277, 5-6: 287, 6-7: 309
    assert_results(measurement, 274, 6.6)


def test_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    instance_name = "20260809_2053"

    measurement = run_measurement_for(coral_name, instance_name)

    # 0-1: 131, 1-2: 131, 2-3: 130, 3-4: 138, 4-5: 140, 5-6: 151, 6-7: 163
    assert_results(measurement, 140, 6.6)


def test_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    instance_name = "20260809_2101"
    
    measurement = run_measurement_for(coral_name, instance_name)

    assert_results(measurement, 99, 23)


def segment(coral_name: str, image_name: str | None = None):
    base_dir = Path(__file__).parents[2]
    if image_name is None:
        path = sorted((base_dir / FIXTURES_DIR / coral_name).glob("*.jpg"))[0]
    else:
        path = base_dir / FIXTURES_DIR / coral_name / image_name
    
    image = cv2.imread(str(path))

    segmentation = fixture_segmenter.segment(image, path.name)
    return image,segmentation

def debug_outputs(coral_name, results):
    print_metrics(coral_name, results)
    cv2.imwrite(f"{datetime.now().strftime('%H%M%S')}_debug_output_{coral_name}.jpg", results["debug_image"])


def print_metrics(coral_name, results):
    print("")
    print("")
    print(f"Results {coral_name}")
    print(f"Detected Scale : {results['px_per_cm']:.2f} pixels/cm")
    print(f"Feret Length   : {results['feret_cm']:.2f} cm")
    print(f"Geodesic Length: {results['geodesic_cm']:.2f} cm")


def assert_results(results: CoralMeasurement, expected_px_per_cm, expected_feret):
    px_per_cm = results.px_per_cm
    expected_px_per_cm_approx = pytest.approx(expected_px_per_cm, rel=PX_PER_CM_ERROR_TOLERANCE_RATIO)
    assert px_per_cm == expected_px_per_cm_approx, f"px per cm assertion failed {px_per_cm} == {expected_px_per_cm_approx}, ratio={round(expected_px_per_cm/px_per_cm, 2)}"

    feret_cm = results.feret_cm
    expected_feret_approx = pytest.approx(expected_feret, abs=FERET_ERROR_TOLERANCE)
    assert feret_cm == expected_feret_approx, f"feret diameter assertion failed {feret_cm} == {expected_feret_approx}, ratio={round(expected_feret/feret_cm, 2)}"
