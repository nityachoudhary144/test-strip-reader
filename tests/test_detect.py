from __future__ import annotations

import numpy as np
import pytest

from strip_reader.detect import (
    UNWRAP_WIDTH,
    find_strip,
    manual_quad,
    order_corners,
    unwrap_strip,
)
from strip_reader.synthetic import demo_strip


def test_find_strip_locates_the_synthetic_strip():
    quad = find_strip(demo_strip())
    assert quad is not None
    assert quad.shape == (4, 2)


def test_find_strip_returns_none_on_an_empty_scene():
    blank = np.full((400, 600, 3), 120, np.uint8)
    assert find_strip(blank) is None


def test_order_corners_returns_a_clockwise_quad_from_top_left():
    points = np.array([[100, 10], [10, 90], [190, 180], [280, 100]], np.float32)
    ordered = order_corners(points)
    assert ordered.shape == (4, 2)
    assert ordered[0][0] < ordered[2][0]
    assert ordered[0][1] < ordered[3][1]


def test_unwrap_strip_returns_the_fixed_target_width():
    image = demo_strip()
    quad = find_strip(image)
    flat = unwrap_strip(image, quad)
    assert flat.shape[1] == UNWRAP_WIDTH
    assert 40 <= flat.shape[0] <= 200


def test_manual_quad_is_axis_aligned_at_zero_degrees():
    quad = manual_quad((100, 200, 3), 0.0, 0.5, 0.5, 0.5, 0.4)
    assert quad.shape == (4, 2)
    assert quad[:, 1].min() == pytest.approx(30.0)
    assert quad[:, 1].max() == pytest.approx(70.0)
    assert quad[:, 0].min() == pytest.approx(50.0)
    assert quad[:, 0].max() == pytest.approx(150.0)


def test_manual_quad_rotates_the_box():
    flat = manual_quad((100, 200, 3), 0.0, 0.5, 0.5, 0.5, 0.4)
    turned = manual_quad((100, 200, 3), 45.0, 0.5, 0.5, 0.5, 0.4)
    assert not np.allclose(flat, turned)
    assert np.allclose(flat.mean(axis=0), turned.mean(axis=0))
