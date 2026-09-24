import pytest

from core.alpha.value_area import value_area


def test_poc_tie_chooses_lower_price_and_expands_to_larger_neighbour():
    profile = {100.0: 10.0, 100.25: 10.0, 100.5: 1.0, 99.75: 2.0}
    # POC tie -> 100.0. Neighbours 100.25 (10) vs 99.75 (2): add 100.25 -> 20/23 = 87% >= 70%.
    assert value_area(profile, 0.70) == (100.0, 100.0, 100.25)


def test_neighbour_tie_adds_lower_price_first():
    profile = {99.75: 5.0, 100.0: 10.0, 100.25: 5.0}
    # 10/20 = 50%; tie between 99.75 and 100.25 adds lower -> 15/20 = 75%.
    assert value_area(profile, 0.70) == (100.0, 99.75, 100.0)


def test_gaps_in_the_price_ladder_are_skipped_not_zero_filled():
    profile = {100.0: 50.0, 101.0: 30.0, 95.0: 20.0}
    # Adjacent traded prices are 95.0 and 101.0; 101.0 has more volume.
    assert value_area(profile, 0.70) == (100.0, 100.0, 101.0)


def test_empty_or_zero_profile_is_rejected():
    with pytest.raises(ValueError):
        value_area({}, 0.70)
    with pytest.raises(ValueError):
        value_area({100.0: 0.0}, 0.70)
