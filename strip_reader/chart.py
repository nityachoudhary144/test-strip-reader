from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    label: str
    rgb: tuple[int, int, int]
    abnormal: bool = False


@dataclass(frozen=True)
class PadSpec:
    name: str
    levels: tuple[Level, ...]


CHART: tuple[PadSpec, ...] = (
    PadSpec(
        "Leukocytes",
        (
            Level("Negative", (247, 243, 224)),
            Level("Trace", (240, 225, 220), True),
            Level("+", (232, 205, 210), True),
            Level("++", (218, 178, 192), True),
            Level("+++", (196, 146, 170), True),
        ),
    ),
    PadSpec(
        "Nitrite",
        (
            Level("Negative", (250, 248, 238)),
            Level("Positive", (233, 170, 172), True),
        ),
    ),
    PadSpec(
        "pH",
        (
            Level("5.0", (238, 190, 105)),
            Level("6.0", (240, 214, 120)),
            Level("6.5", (222, 222, 140)),
            Level("7.0", (176, 205, 140)),
            Level("8.0", (120, 175, 165), True),
            Level("8.5", (95, 150, 190), True),
        ),
    ),
    PadSpec(
        "Protein",
        (
            Level("Negative", (240, 242, 214)),
            Level("Trace", (225, 232, 190), True),
            Level("+", (205, 220, 160), True),
            Level("++", (180, 205, 135), True),
            Level("+++", (155, 190, 110), True),
        ),
    ),
    PadSpec(
        "Blood",
        (
            Level("Negative", (242, 236, 178)),
            Level("Trace", (215, 220, 150), True),
            Level("+", (165, 195, 120), True),
            Level("++", (110, 155, 105), True),
            Level("+++", (70, 110, 95), True),
        ),
    ),
    PadSpec(
        "Glucose",
        (
            Level("Negative", (206, 232, 200)),
            Level("Trace", (192, 222, 175), True),
            Level("+", (175, 205, 140), True),
            Level("++", (160, 185, 105), True),
            Level("+++", (145, 160, 75), True),
        ),
    ),
)

DEMO_PLAN = (3, 1, 4, 1, 2, 0)
