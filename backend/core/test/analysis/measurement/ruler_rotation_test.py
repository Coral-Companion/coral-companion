import cv2
from pathlib import Path
from app.analysis.measurement.ruler_rotation import RulerRotation
from app.analysis.measurement.models import RotatedRuler
import app.utils.fixtures as fixtures

FIXTURES_DIR = Path("dev_fixtures")

ruler_rotation = RulerRotation()
save_pickles = True

def test_measure_algalpavona():
    coral_name = "unknown_algalpavona"
    specific = "20260811_1636"
    rotate_for(coral_name, specific)

def test_measure_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    specific = "20260809_2059"
    rotate_for(coral_name, specific)


def test_measure_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260809_2100"
    rotate_for(coral_name, specific)


def test_measure_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260811_1638"
    rotate_for(coral_name, specific)


def test_measure_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    specific = "20260811_1637_branchypavona"
    rotate_for(coral_name, specific)


def test_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260809_1943"
    rotate_for(coral_name, specific)


def test_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1638_darkpocillopora"
    rotate_for(coral_name, specific)


def test_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1639_darkpocillopora"
    rotate_for(coral_name, specific)


def test_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    specific = "20260809_2053"
    rotate_for(coral_name, specific)


def test_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    specific = "20260809_2101"
    rotate_for(coral_name, specific)


def test_leasoned_porites():
    coral_name = "unknown_lesionedporites"
    specific = "20260811_1642"
    rotate_for(coral_name, specific)


def test_tiger_pavona():
    coral_name = "unknown_tigerpavona"
    specific = "20260811_1646"
    rotate_for(coral_name, specific)


def test_octo_pavona():
    coral_name = "unknown_octopavona"
    specific = "20260811_1642"
    rotate_for(coral_name, specific)


def test_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260811_1644"
    rotate_for(coral_name, specific)


def test_darth_porites():
    coral_name = "unknown_darthporites"
    specific = "20260811_1639"
    rotate_for(coral_name, specific)


def test_spongy_pocillopora():
    coral_name = "unknown_spongypocillopora"
    specific = "20260811_1645"
    rotate_for(coral_name, specific)


def test_measure_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260819_1813"
    rotate_for(coral_name, specific)


def rotate_for(coral_name: str, instance: str):
    image = load_image(coral_name, f"{instance}.jpg")
    geometry = fixtures.load_pickle(coral_name, f"ruler_geometry_{instance}")
    debug_name = f"{coral_name}_{instance}"
    
    results = ruler_rotation.rotate_ruler(image, geometry.mask, geometry, debug_name)
    
    debug_outputs(results)
    if save_pickles: fixtures.save_pickle(coral_name, f"ruler_rotation_{instance}", results)

def load_image(coral_name: str, image_name: str | None = None):
    base_dir = Path(__file__).parents[3]
    if image_name is None:
        path = sorted((base_dir / FIXTURES_DIR / coral_name).glob("*.jpg"))[0]
    else:
        path = base_dir / FIXTURES_DIR / coral_name / image_name
    image = cv2.imread(str(path))
    return image

def debug_outputs(results: RotatedRuler):
    print(f"tbd")
