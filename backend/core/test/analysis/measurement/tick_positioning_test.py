from app.analysis.measurement.models import TickPositions
from app.analysis.measurement.tick_positioning import TickPositioning
import app.utils.fixtures as fixtures
import numpy as np

tick_positioning = TickPositioning()
save_pickles = True

def test_position_ticks_algalpavona():
    coral_name = "unknown_algalpavona"
    specific = "20260811_1636"
    position_ticks_for(coral_name, specific)
    

def test_position_ticks_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    specific = "20260809_2059"
    position_ticks_for(coral_name, specific)


def test_position_ticks_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260809_2100"
    position_ticks_for(coral_name, specific)


def test_position_ticks_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260811_1638"
    position_ticks_for(coral_name, specific)


def test_position_ticks_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    specific = "20260811_1637_branchypavona"
    position_ticks_for(coral_name, specific)


def test_position_ticks_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260809_1943"
    position_ticks_for(coral_name, specific)


def test_position_ticks_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1638_darkpocillopora"
    position_ticks_for(coral_name, specific)


def test_position_ticks_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1639_darkpocillopora"
    position_ticks_for(coral_name, specific)


def test_position_ticks_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    specific = "20260809_2053"
    position_ticks_for(coral_name, specific)


def test_position_ticks_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    specific = "20260809_2101"
    position_ticks_for(coral_name, specific)


def test_position_ticks_leasoned_porites():
    coral_name = "unknown_lesionedporites"
    specific = "20260811_1642"
    position_ticks_for(coral_name, specific)


def test_position_ticks_tiger_pavona():
    coral_name = "unknown_tigerpavona"
    specific = "20260811_1646"
    position_ticks_for(coral_name, specific)


def test_position_ticks_octo_pavona():
    coral_name = "unknown_octopavona"
    specific = "20260811_1642"
    position_ticks_for(coral_name, specific)


def test_position_ticks_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260811_1644"
    position_ticks_for(coral_name, specific)


def test_position_ticks_darth_porites():
    coral_name = "unknown_darthporites"
    specific = "20260811_1639"
    position_ticks_for(coral_name, specific)


def test_position_ticks_spongy_pocillopora():
    coral_name = "unknown_spongypocillopora"
    specific = "20260811_1645"
    position_ticks_for(coral_name, specific)

def test_measure_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    instance_name = "20260819_1813"
    position_ticks_for(coral_name, instance_name)

def position_ticks_for(coral_name: str, instance: str):
    detection = fixtures.load_pickle(coral_name, f"tick_detection_{instance}")
    rotated_ruler = fixtures.load_pickle(coral_name, f"ruler_rotation_{instance}")
    debug_name = f"{coral_name}_{instance}"
    
    positions = tick_positioning.find_tick_positions(detection=detection, name_for_debug=debug_name, rotated_ruler_for_debug=rotated_ruler)
    
    if save_pickles: fixtures.save_pickle(coral_name, f"tick_positioning_{instance}", positions)
    
def debug_outputs(results: TickPositions):
    print(f"Positions: {results.positions}")
    print()
    print()
