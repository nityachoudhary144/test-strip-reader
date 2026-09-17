from __future__ import annotations

import numpy as np

CELL_MARGIN = 0.25
BAND_TOP = 0.20
BAND_BOTTOM = 0.80


def sample_pads(
    strip: np.ndarray,
    pad_count: int,
    pad_start: float = 0.0,
    pad_end: float = 1.0,
) -> np.ndarray:
    if pad_count < 1:
        raise ValueError("pad_count must be at least 1")

    height, width = strip.shape[:2]

    band_start = int(np.clip(pad_start, 0.0, 0.99) * width)
    band_end = int(np.clip(pad_end, 0.01, 1.0) * width)
    band_end = max(band_end, band_start + 1)
    cell_width = (band_end - band_start) / pad_count

    colours = np.zeros((pad_count, 3), dtype=np.float64)
    for index in range(pad_count):
        x0 = int(band_start + index * cell_width + CELL_MARGIN * cell_width)
        x1 = int(band_start + (index + 1) * cell_width - CELL_MARGIN * cell_width)
        y0 = int(BAND_TOP * height)
        y1 = int(BAND_BOTTOM * height)

        patch = strip[y0:y1, max(x0, 0) : max(x1, x0 + 1)]
        if patch.size == 0:
            patch = strip

        colours[index] = np.median(patch.reshape(-1, 3).astype(np.float64), axis=0)

    return colours
