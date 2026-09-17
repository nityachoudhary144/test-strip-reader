from __future__ import annotations

import numpy as np
import pytest

from strip_reader.chart import CHART
from strip_reader.detect import find_strip
from strip_reader.synthetic import expected_labels, demo_strip


def test_demo_strip_is_deterministic():
    assert np.array_equal(demo_strip(), demo_strip())


def test_demo_strip_angle_changes_the_pixels():
    assert not np.array_equal(demo_strip(angle=0.0), demo_strip(angle=12.0))


def test_demo_strip_is_detectable_at_the_documented_angles():
    for angle in (-12.0, -4.0, 0.0, 4.0, 12.0):
        assert find_strip(demo_strip(angle=angle)) is not None


def test_demo_strip_stays_inside_the_canvas():
    image = demo_strip(angle=20.0)
    assert image.shape == (520, 900, 3)
    assert image.dtype == np.uint8


def test_demo_strip_rejects_a_non_positive_pad_count():
    with pytest.raises(ValueError):
        demo_strip(pad_count=0)


def test_expected_labels_follows_the_chart():
    labels = expected_labels()
    assert len(labels) == len(CHART)
    assert all(
        label in [level.label for level in spec.levels]
        for label, spec in zip(labels, CHART)
    )


def test_expected_labels_wraps_for_extra_pads():
    assert len(expected_labels(len(CHART) + 3)) == len(CHART) + 3
