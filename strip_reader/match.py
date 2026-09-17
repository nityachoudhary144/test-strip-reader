from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from strip_reader.chart import CHART, PadSpec
from strip_reader.colour import delta_e, rgb_to_lab

GOOD_MATCH = 8.0
FAIR_MATCH = 15.0


@dataclass
class PadReading:
    name: str
    value: str
    abnormal: bool
    delta_e: float
    rgb: tuple[int, int, int]

    @property
    def confidence(self) -> str:
        if self.delta_e <= GOOD_MATCH:
            return "good"
        if self.delta_e <= FAIR_MATCH:
            return "fair"
        return "poor"


def classify(colour: np.ndarray, spec: PadSpec) -> tuple[str, bool, float]:
    bgr = np.clip(colour, 0, 255).astype(np.uint8)
    lab = rgb_to_lab((int(bgr[2]), int(bgr[1]), int(bgr[0])))

    best = spec.levels[0]
    best_distance = float("inf")
    for level in spec.levels:
        distance = delta_e(lab, rgb_to_lab(level.rgb))
        if distance < best_distance:
            best_distance = distance
            best = level

    return best.label, best.abnormal, best_distance


def match_pads(colours: np.ndarray, chart: tuple[PadSpec, ...] = CHART) -> list[PadReading]:
    readings: list[PadReading] = []

    for index, colour in enumerate(colours):
        spec = chart[index % len(chart)]
        label, abnormal, distance = classify(colour, spec)
        bgr = np.clip(colour, 0, 255).astype(np.uint8)

        readings.append(
            PadReading(
                name=spec.name,
                value=label,
                abnormal=abnormal,
                delta_e=distance,
                rgb=(int(bgr[2]), int(bgr[1]), int(bgr[0])),
            )
        )

    return readings
