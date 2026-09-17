from __future__ import annotations

import numpy as np

from strip_reader.analyzer import NO_STRIP_MESSAGE, analyze
from strip_reader.chart import CHART
from strip_reader.detect import manual_quad
from strip_reader.synthetic import DEMO_PAD_START, demo_strip, expected_labels


def analysed_demo():
    return analyze(demo_strip(), pad_start=DEMO_PAD_START)


def test_analyze_reads_every_pad_on_the_synthetic_strip():
    result = analysed_demo()
    assert result.ok is True
    assert len(result.readings) == len(CHART)
    assert [r.value for r in result.readings] == expected_labels()


def test_analyze_returns_the_intermediate_images():
    result = analysed_demo()
    assert result.quad.shape == (4, 2)
    assert result.unwrapped is not None
    assert result.annotated is not None
    assert result.annotated.shape[1] == demo_strip().shape[1]


def test_analyze_reports_a_missing_strip_instead_of_raising():
    blank = np.full((400, 600, 3), 100, np.uint8)
    result = analyze(blank)
    assert result.ok is False
    assert result.message == NO_STRIP_MESSAGE
    assert result.readings == []


def test_analyze_rejects_an_empty_image():
    result = analyze(np.zeros((0, 0, 3), np.uint8))
    assert result.ok is False
    assert result.message == "Empty image."


def test_analyze_accepts_a_caller_supplied_quad():
    image = demo_strip(angle=0.0)
    quad = manual_quad(image.shape, 0.0, 0.5, 0.5, 0.78, 0.21)
    result = analyze(image, quad=quad, pad_start=DEMO_PAD_START)
    assert result.ok is True
    assert np.allclose(result.quad, quad)


def test_analysis_is_repeatable_for_the_same_input():
    first = analysed_demo()
    second = analysed_demo()
    assert [r.value for r in first.readings] == [r.value for r in second.readings]
    assert np.allclose(
        [r.delta_e for r in first.readings], [r.delta_e for r in second.readings]
    )


def test_abnormal_property_lists_only_out_of_range_pads():
    result = analysed_demo()
    abnormal = result.abnormal
    assert all(reading.abnormal for reading in abnormal)
    assert len(abnormal) == sum(1 for r in result.readings if r.abnormal)


def test_pad_count_changes_the_number_of_readings():
    result = analyze(demo_strip(pad_count=3), pad_count=3, pad_start=DEMO_PAD_START)
    assert result.ok is True
    assert len(result.readings) == 3


def test_white_balance_can_be_disabled():
    image = demo_strip()
    assert analyze(image, calibrate=False, pad_start=DEMO_PAD_START).calibrated is False
    assert analyze(image, calibrate=True, pad_start=DEMO_PAD_START).calibrated is True
