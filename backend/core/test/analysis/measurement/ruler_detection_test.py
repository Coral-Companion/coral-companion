import cv2
from pathlib import Path
from app.analysis.measurement.ruler_detection import RulerDetection
from app.analysis.measurement.models import RulerGeometry
import app.utils.fixtures as fixtures

FIXTURES_DIR = Path("dev_fixtures")

ruler_detection = RulerDetection()
save_pickles = True

def measure_for(coral_name, instance):
    image = load_image(coral_name, f"{instance}.jpg")
    results = ruler_detection.detect_ruler(image, f"{coral_name.replace('unknown_', '')}_{instance}")
    debug_outputs(results)
    if save_pickles: fixtures.save_pickle(coral_name, f"ruler_geometry_{instance}", results)


def test_measure_algalpavona():
    coral_name = "unknown_algalpavona"
    specific = "20260811_1636"
    measure_for(coral_name, specific)


def test_measure_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    specific = "20260809_2059"
    measure_for(coral_name, specific)


def test_measure_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260809_2100"
    measure_for(coral_name, specific)


def test_measure_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260811_1638"
    measure_for(coral_name, specific)


def test_measure_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    specific = "20260811_1637_branchypavona"
    measure_for(coral_name, specific)


def test_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260809_1943"
    measure_for(coral_name, specific)


def test_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1638_darkpocillopora"
    measure_for(coral_name, specific)


def test_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1639_darkpocillopora"
    measure_for(coral_name, specific)


def test_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    specific = "20260809_2053"
    measure_for(coral_name, specific)


def test_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    specific = "20260809_2101"
    measure_for(coral_name, specific)


def test_leasoned_porites():
    coral_name = "unknown_lesionedporites"
    specific = "20260811_1642"
    measure_for(coral_name, specific)


def test_tiger_pavona():
    coral_name = "unknown_tigerpavona"
    specific = "20260811_1646"
    measure_for(coral_name, specific)


def test_octo_pavona():
    coral_name = "unknown_octopavona"
    specific = "20260811_1642"
    measure_for(coral_name, specific)


def test_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260811_1644"
    measure_for(coral_name, specific)


def test_darth_porites():
    coral_name = "unknown_darthporites"
    specific = "20260811_1639"
    measure_for(coral_name, specific)


def test_spongy_pocillopora():
    coral_name = "unknown_spongypocillopora"
    specific = "20260811_1645"
    measure_for(coral_name, specific)

def test_snuggly_porites_high_def_image():
    coral_name = "unknown_snugglyporites"
    instance_name = "20260819_1813"
    measure_for(coral_name, instance_name)

def load_image(coral_name: str, image_name: str | None = None):
    base_dir = Path(__file__).parents[3]
    if image_name is None:
        path = sorted((base_dir / FIXTURES_DIR / coral_name).glob("*.jpg"))[0]
    else:
        path = base_dir / FIXTURES_DIR / coral_name / image_name
    image = cv2.imread(str(path))
    return image

def debug_outputs(results: RulerGeometry):
    print(f"Angle  : {results.angle_degrees}")
    print(f"Center : {results.center}")
    print(f"Height : {results.height}")
    print(f"Width  : {results.width}")
    
def dev_fixture_path_for_coral(coral_name: str) -> Path:
    base_dir = Path(__file__).parents[3]
    return base_dir / FIXTURES_DIR / coral_name
