from __future__ import annotations

import numpy as np
import pytest

from strip_reader.sample import sample_pads


def painted_strip(pad_colours, width=600, height=100):
    strip = np.zeros((height, width, 3), np.uint8)
    cell = width // len(pad_colours)
    for index, colour in enumerate(pad_colours):
        strip[:, index * cell : (index + 1) * cell] = colour
    return strip


def test_sample_pads_recovers_painted_colours():
    painted = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    colours = sample_pads(painted_strip(painted), len(painted))
    assert colours.shape == (3, 3)
    for measured, want in zip(colours, painted):
        assert np.allclose(measured, want, atol=1.0)


def test_sample_pads_survives_a_specular_highlight():
    strip = painted_strip([(200, 200, 200)])
    strip[10:20, 10:20] = 255
    colours = sample_pads(strip, 1)
    assert np.allclose(colours[0], (200, 200, 200), atol=1.0)


def test_sample_pads_respects_the_pad_band():
    strip = np.zeros((100, 600, 3), np.uint8)
    strip[:, :300] = (0, 0, 255)
    strip[:, 300:] = (255, 0, 0)

    left_half = sample_pads(strip, 1, pad_start=0.0, pad_end=0.5)
    right_half = sample_pads(strip, 1, pad_start=0.5, pad_end=1.0)
    assert np.allclose(left_half[0], (0, 0, 255), atol=1.0)
    assert np.allclose(right_half[0], (255, 0, 0), atol=1.0)


def test_sample_pads_rejects_a_non_positive_count():
    with pytest.raises(ValueError):
        sample_pads(painted_strip([(0, 0, 0)]), 0)
