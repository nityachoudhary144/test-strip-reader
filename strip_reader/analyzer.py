from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from strip_reader.annotate import overlay
from strip_reader.chart import CHART, PadSpec
from strip_reader.colour import white_balance
from strip_reader.detect import find_strip, unwrap_strip
from strip_reader.match import PadReading, match_pads
from strip_reader.sample import sample_pads

NO_STRIP_MESSAGE = (
    "No strip found. Put it on a plain, contrasting background, fill "
    "the frame and try again, or switch on manual mode."
)


@dataclass
class StripResult:
    ok: bool
    message: str = ""
    readings: list[PadReading] = field(default_factory=list)
    quad: np.ndarray | None = None
    unwrapped: np.ndarray | None = None
    annotated: np.ndarray | None = None
    calibrated: bool = False

    @property
    def abnormal(self) -> list[PadReading]:
        return [reading for reading in self.readings if reading.abnormal]

    @property
    def poor_matches(self) -> list[PadReading]:
        return [reading for reading in self.readings if reading.confidence == "poor"]


def analyze(
    bgr: np.ndarray,
    pad_count: int = len(CHART),
    calibrate: bool = True,
    quad: np.ndarray | None = None,
    pad_start: float = 0.0,
    pad_end: float = 1.0,
    chart: tuple[PadSpec, ...] = CHART,
) -> StripResult:
    if bgr is None or bgr.size == 0:
        return StripResult(ok=False, message="Empty image.")

    if quad is None:
        detected = find_strip(bgr)
        if detected is None:
            return StripResult(ok=False, message=NO_STRIP_MESSAGE)
        quad = detected

    strip = unwrap_strip(bgr, quad)
    colours = sample_pads(strip, pad_count, pad_start, pad_end)

    calibrated = False
    if calibrate:
        colours, calibrated = white_balance(colours, strip)

    readings = match_pads(colours, chart)

    return StripResult(
        ok=True,
        readings=readings,
        quad=np.asarray(quad, dtype=np.float32),
        unwrapped=strip,
        annotated=overlay(bgr, quad, readings),
        calibrated=calibrated,
    )
