from __future__ import annotations

import cv2
import numpy as np

from strip_reader.chart import CHART, DEMO_PLAN, PadSpec

DEMO_PAD_START = 0.14
DEMO_SIZE = (520, 900)
DEMO_STRIP_SIZE = (700, 110)
DEMO_BACKGROUND = (48, 58, 52)
DEMO_PAD_INSET = 0.12
DEMO_PAD_VERTICAL_INSET = 14
DEMO_NOISE = 3.0
DEMO_SEED = 7
DEMO_ANGLE = 6.0


def spec_at(chart: tuple[PadSpec, ...], index: int) -> PadSpec:
    return chart[index % len(chart)]


def level_index(spec: PadSpec, plan: tuple[int, ...], index: int) -> int:
    return plan[index % len(plan)] % len(spec.levels)


def demo_strip(
    pad_count: int = len(CHART),
    angle: float = DEMO_ANGLE,
    background: tuple[int, int, int] = DEMO_BACKGROUND,
    chart: tuple[PadSpec, ...] = CHART,
    plan: tuple[int, ...] = DEMO_PLAN,
) -> np.ndarray:
    if pad_count < 1:
        raise ValueError("pad_count must be at least 1")

    height, width = DEMO_SIZE
    canvas = np.full((height, width, 3), background, np.uint8)

    strip_w, strip_h = DEMO_STRIP_SIZE
    strip = np.full((strip_h, strip_w, 3), 250, np.uint8)

    handle = int(strip_w * DEMO_PAD_START)
    cell = (strip_w - handle) / pad_count

    rng = np.random.default_rng(DEMO_SEED)
    for index in range(pad_count):
        spec = spec_at(chart, index)
        level = spec.levels[level_index(spec, plan, index)]
        colour = np.array(level.rgb[::-1], np.float64) + rng.normal(0, DEMO_NOISE, 3)

        x0 = int(handle + index * cell + DEMO_PAD_INSET * cell)
        x1 = int(handle + (index + 1) * cell - DEMO_PAD_INSET * cell)
        strip[
            DEMO_PAD_VERTICAL_INSET : strip_h - DEMO_PAD_VERTICAL_INSET, x0:x1
        ] = np.clip(colour, 0, 255).astype(np.uint8)

    matrix = cv2.getRotationMatrix2D((strip_w / 2, strip_h / 2), angle, 1.0)
    matrix[0, 2] += (width - strip_w) / 2
    matrix[1, 2] += (height - strip_h) / 2

    rotated = cv2.warpAffine(strip, matrix, (width, height), borderValue=background)
    mask = cv2.warpAffine(
        np.full((strip_h, strip_w), 255, np.uint8), matrix, (width, height)
    )
    canvas[mask > 0] = rotated[mask > 0]
    return canvas


def expected_labels(
    pad_count: int = len(CHART),
    chart: tuple[PadSpec, ...] = CHART,
    plan: tuple[int, ...] = DEMO_PLAN,
) -> list[str]:
    labels = []
    for index in range(pad_count):
        spec = spec_at(chart, index)
        labels.append(spec.levels[level_index(spec, plan, index)].label)
    return labels
