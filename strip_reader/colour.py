from __future__ import annotations

import cv2
import numpy as np

TARGET_WHITE = 245.0
MIN_REFERENCE_PIXELS = 20


def rgb_to_lab(rgb) -> np.ndarray:
    arr = np.uint8([[list(rgb)]])
    return cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)[0, 0].astype(np.float64)


def delta_e(lab_a: np.ndarray, lab_b: np.ndarray) -> float:
    return float(np.linalg.norm(lab_a - lab_b))


def white_balance(colours: np.ndarray, strip: np.ndarray) -> tuple[np.ndarray, bool]:
    pixels = strip.reshape(-1, 3).astype(np.float32)
    hsv = cv2.cvtColor(strip, cv2.COLOR_BGR2HSV).reshape(-1, 3)

    bright = hsv[:, 2] >= np.percentile(hsv[:, 2], 90)
    neutral = hsv[:, 1] <= np.percentile(hsv[:, 1], 50)
    reference_pixels = pixels[bright & neutral]
    if reference_pixels.shape[0] < MIN_REFERENCE_PIXELS:
        return colours, False

    reference = np.median(reference_pixels, axis=0)
    if np.any(reference < 30):
        return colours, False

    gain = np.clip(TARGET_WHITE / reference, 0.5, 2.0)
    return np.clip(colours * gain, 0, 255), True
