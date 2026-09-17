from __future__ import annotations

import numpy as np
import pytest

from strip_reader.chart import CHART
from strip_reader.colour import delta_e, rgb_to_lab, white_balance


def test_rgb_to_lab_reference_values():
    assert np.allclose(rgb_to_lab((255, 255, 255)), (255.0, 128.0, 128.0))
    assert np.allclose(rgb_to_lab((0, 0, 0)), (0.0, 128.0, 128.0))


def test_delta_e_is_zero_for_identical_colours():
    lab = rgb_to_lab((120, 80, 60))
    assert delta_e(lab, lab) == pytest.approx(0.0)


def test_delta_e_is_symmetric_and_positive():
    a = rgb_to_lab((200, 30, 30))
    b = rgb_to_lab((30, 200, 30))
    assert delta_e(a, b) == pytest.approx(delta_e(b, a))
    assert delta_e(a, b) > 0


def test_white_balance_maps_the_strip_reference_to_a_neutral_white():
    reference = np.array([150.0, 180.0, 230.0])
    strip = np.full((60, 600, 3), reference.astype(np.uint8), np.uint8)
    colours = np.tile(reference, (2, 1))

    balanced, ok = white_balance(colours, strip)
    assert ok is True
    assert balanced.std(axis=1).max() < 1.0
    assert np.allclose(balanced[0], 245.0, atol=1.0)


def test_white_balance_reports_failure_without_neutral_pixels():
    strip = np.full((4, 4, 3), (0, 0, 250), np.uint8)
    colours = np.full((6, 3), 200.0)
    balanced, ok = white_balance(colours, strip)
    assert ok is False
    assert np.allclose(balanced, colours)


def test_chart_levels_are_unique_and_ordered_from_negative():
    for spec in CHART:
        labels = [level.label for level in spec.levels]
        assert len(labels) == len(set(labels))
        assert spec.levels[0].abnormal is False
