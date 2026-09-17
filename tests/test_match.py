from __future__ import annotations

import numpy as np

from strip_reader.chart import CHART, Level, PadSpec
from strip_reader.match import FAIR_MATCH, GOOD_MATCH, classify, match_pads


def test_classify_returns_the_exact_level_with_zero_distance():
    spec = PadSpec("Probe", (Level("A", (10, 20, 30)), Level("B", (200, 210, 220), True)))
    label, abnormal, distance = classify(np.array([30.0, 20.0, 10.0]), spec)
    assert label == "A"
    assert abnormal is False
    assert distance < 1.0


def test_classify_picks_the_nearest_level_and_flags_abnormal():
    spec = PadSpec("Probe", (Level("A", (10, 20, 30)), Level("B", (200, 210, 220), True)))
    label, abnormal, distance = classify(np.array([222.0, 212.0, 202.0]), spec)
    assert label == "B"
    assert abnormal is True
    assert distance < 5.0


def test_match_pads_preserves_chart_order_and_length():
    colours = np.full((len(CHART), 3), 128.0)
    readings = match_pads(colours)
    assert len(readings) == len(CHART)
    assert [reading.name for reading in readings] == [spec.name for spec in CHART]


def test_match_pads_wraps_when_more_pads_than_chart_entries():
    readings = match_pads(np.full((len(CHART) + 2, 3), 128.0))
    assert len(readings) == len(CHART) + 2
    assert readings[-1].name == CHART[1].name


def test_confidence_bands_follow_the_delta_e_thresholds():
    readings = match_pads(np.full((3, 3), 128.0))
    assert GOOD_MATCH < FAIR_MATCH
    for reading in readings:
        if reading.delta_e <= GOOD_MATCH:
            assert reading.confidence == "good"
        elif reading.delta_e <= FAIR_MATCH:
            assert reading.confidence == "fair"
        else:
            assert reading.confidence == "poor"


def test_matching_returns_an_rgb_tuple():
    readings = match_pads(np.array([[30.0, 20.0, 10.0]]))
    assert readings[0].rgb == (10, 20, 30)
