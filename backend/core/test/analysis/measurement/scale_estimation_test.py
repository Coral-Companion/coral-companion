from app.analysis.measurement.models import RulerScale
from app.analysis.measurement.scale_estimation import ScaleEstimation
import app.utils.fixtures as fixtures
import numpy as np

scale_estimation = ScaleEstimation()
save_pickles = True

def test_estimate_ruler_algalpavona():
    coral_name = "unknown_algalpavona"
    specific = "20260811_1636"
    estimate_ruler_scale_for(coral_name, specific)
    

def test_estimate_ruler_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    specific = "20260809_2059"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260809_2100"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260811_1638"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    specific = "20260811_1637_branchypavona"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260809_1943"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1638_darkpocillopora"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1639_darkpocillopora"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    specific = "20260809_2053"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    specific = "20260809_2101"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_leasoned_porites():
    coral_name = "unknown_lesionedporites"
    specific = "20260811_1642"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_tiger_pavona():
    coral_name = "unknown_tigerpavona"
    specific = "20260811_1646"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_octo_pavona():
    coral_name = "unknown_octopavona"
    specific = "20260811_1642"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260811_1644"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_darth_porites():
    coral_name = "unknown_darthporites"
    specific = "20260811_1639"
    estimate_ruler_scale_for(coral_name, specific)


def test_estimate_ruler_spongy_pocillopora():
    coral_name = "unknown_spongypocillopora"
    specific = "20260811_1645"
    estimate_ruler_scale_for(coral_name, specific)

def test_estimate_ruler_snuggly_porites_hd():
    coral_name = "unknown_snugglyporites"
    instance_name = "20260819_1813"
    estimate_ruler_scale_for(coral_name, instance_name)

def estimate_ruler_scale_for(coral_name: str, instance: str):
    tick_positions = fixtures.load_pickle(coral_name, f"tick_positioning_{instance}")
    rotated_ruler = fixtures.load_pickle(coral_name, f"ruler_rotation_{instance}")
    debug_name = f"{coral_name}_{instance}"
    
    ruler_scale = scale_estimation.estimate_ruler_scale(tick_positions=tick_positions, name_for_debug=debug_name, rotated_ruler=rotated_ruler)
    
    if save_pickles: fixtures.save_pickle(coral_name, f"scale_estimation_{instance}", ruler_scale)
    
    debug_outputs(ruler_scale)

def debug_outputs(results: RulerScale):
    print(f"Pixels per mm: {results.pixels_per_mm}")
    print()
    print()
