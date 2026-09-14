import cv2
from pathlib import Path
from app.analysis.measurement.tick_detection import TickDetection
from app.analysis.measurement.models import TickSignals
import app.utils.fixtures as fixtures
from functools import partial
import numpy as np

FIXTURES_DIR = Path("dev_fixtures")

tick_detection = TickDetection(
    threshold_percentile=90,
    signal_aggregation=np.median,
    sobel_kernel_size=3
)
save_pickles = True

def test_detect_ticks_algalpavona():
    coral_name = "unknown_algalpavona"
    specific = "20260811_1636"
    detect_ticks_for(coral_name, specific)
    

def test_detect_ticks_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    specific = "20260809_2059"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260809_2100"
    detect_ticks_for(coral_name, specific)


# TODO: this is detected poorly
def test_detect_ticks_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260811_1638"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    specific = "20260811_1637_branchypavona"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260809_1943"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1638_darkpocillopora"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1639_darkpocillopora"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    specific = "20260809_2053"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    specific = "20260809_2101"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_leasoned_porites():
    coral_name = "unknown_lesionedporites"
    specific = "20260811_1642"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_tiger_pavona():
    coral_name = "unknown_tigerpavona"
    specific = "20260811_1646"
    detect_ticks_for(coral_name, specific)


# TODO: this one is detected poorly
def test_detect_ticks_octo_pavona():
    coral_name = "unknown_octopavona"
    specific = "20260811_1642"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260811_1644"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_darth_porites():
    coral_name = "unknown_darthporites"
    specific = "20260811_1639"
    detect_ticks_for(coral_name, specific)


def test_detect_ticks_spongy_pocillopora():
    coral_name = "unknown_spongypocillopora"
    specific = "20260811_1645"
    detect_ticks_for(coral_name, specific)


def test_measure_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260819_1813"
    detect_ticks_for(coral_name, specific)
    

def detect_ticks_for(coral_name: str, instance: str):
    rotation = fixtures.load_pickle(coral_name, f"ruler_rotation_{instance}")
    debug_name = f"{coral_name}_{instance}"
    
    results = tick_detection.detect_ticks(rotated_ruler=rotation, name_for_debug=debug_name)
    
    debug_outputs(results)
    if save_pickles: fixtures.save_pickle(coral_name, f"tick_detection_{instance}", results)

def load_image(coral_name: str, image_name: str | None = None):
    base_dir = Path(__file__).parents[3]
    if image_name is None:
        path = sorted((base_dir / FIXTURES_DIR / coral_name).glob("*.jpg"))[0]
    else:
        path = base_dir / FIXTURES_DIR / coral_name / image_name
    image = cv2.imread(str(path))
    return image

def debug_outputs(results: TickSignals):
    print(f"Threshold: {results.threshold}")
    print()
    print()
