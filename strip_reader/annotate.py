from __future__ import annotations

import cv2
import numpy as np

from strip_reader.detect import order_corners
from strip_reader.match import PadReading

OVERLAY_COLOUR = (0, 200, 0)
CORNER_COLOUR = (0, 165, 255)
BAR_COLOUR = 30
BAR_HEIGHT = 46
CORNER_RADIUS = 7
SWATCH_WIDTH = 90
SWATCH_HEIGHT = 60
SWATCH_GAP = 6


def overlay(bgr: np.ndarray, quad: np.ndarray, readings: list[PadReading]) -> np.ndarray:
    canvas = bgr.copy()
    corners = order_corners(quad).astype(np.int32)

    cv2.polylines(canvas, [corners], True, OVERLAY_COLOUR, 3)
    cv2.circle(canvas, tuple(corners[0]), CORNER_RADIUS, CORNER_COLOUR, -1)

    bar = np.full((BAR_HEIGHT, canvas.shape[1], 3), BAR_COLOUR, np.uint8)
    slot = canvas.shape[1] // max(len(readings), 1)
    for index, reading in enumerate(readings):
        x0 = index * slot
        bar[:, x0 : x0 + slot - 4] = (reading.rgb[2], reading.rgb[1], reading.rgb[0])

    return np.vstack([canvas, bar])


def swatch_strip(readings: list[PadReading]) -> np.ndarray:
    canvas = np.full(
        (SWATCH_HEIGHT, SWATCH_WIDTH * len(readings), 3),
        255,
        np.uint8,
    )
    for index, reading in enumerate(readings):
        x0 = index * SWATCH_WIDTH
        canvas[:, x0 : x0 + SWATCH_WIDTH - SWATCH_GAP] = (
            reading.rgb[2],
            reading.rgb[1],
            reading.rgb[0],
        )
    return canvas
