from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

UNWRAP_WIDTH = 760
UNWRAP_MAX_HEIGHT = 200
BG_DISTANCE = 45
MIN_AREA_FRACTION = 0.015
MIN_ELONGATION = 1.5

TARGET_WHITE = 245.0

GOOD_MATCH = 8.0
FAIR_MATCH = 15.0

DEMO_PLAN = (3, 1, 4, 1, 2, 0)
DEMO_PAD_START = 0.14


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


@dataclass
class StripResult:
    ok: bool
    message: str = ""
    readings: list[PadReading] = field(default_factory=list)
    quad: np.ndarray | None = None
    unwrapped: np.ndarray | None = None
    annotated: np.ndarray | None = None
    calibrated: bool = False


def rgb_to_lab(rgb) -> np.ndarray:
    arr = np.uint8([[list(rgb)]])
    return cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)[0, 0].astype(np.float64)


def delta_e(lab_a: np.ndarray, lab_b: np.ndarray) -> float:
    return float(np.linalg.norm(lab_a - lab_b))


def _background_colour(bgr: np.ndarray) -> np.ndarray:
    edge = 10
    rings = [
        bgr[:edge].reshape(-1, 3),
        bgr[-edge:].reshape(-1, 3),
        bgr[:, :edge].reshape(-1, 3),
        bgr[:, -edge:].reshape(-1, 3),
    ]
    return np.median(np.concatenate(rings), axis=0)


def find_strip(bgr: np.ndarray) -> np.ndarray | None:
    height, width = bgr.shape[:2]

    background = _background_colour(bgr)
    distance = np.linalg.norm(bgr.astype(np.float32) - background, axis=2)
    mask = ((distance > BG_DISTANCE) * 255).astype(np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_AREA_FRACTION * height * width:
            continue

        rect = cv2.minAreaRect(contour)
        (_, _), (rect_w, rect_h), _ = rect
        long_side, short_side = max(rect_w, rect_h), min(rect_w, rect_h)
        if short_side < 1 or long_side / short_side < MIN_ELONGATION:
            continue

        if area > best_area:
            best_area = area
            best = rect

    return None if best is None else cv2.boxPoints(best).astype(np.float32)


def _order_corners(points: np.ndarray) -> np.ndarray:
    centroid = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - centroid[1], points[:, 0] - centroid[0])
    ordered = points[np.argsort(angles)]

    if np.linalg.norm(ordered[2] - ordered[1]) > np.linalg.norm(ordered[1] - ordered[0]):
        ordered = np.roll(ordered, -1, axis=0)

    if ordered[0][0] > ordered[2][0]:
        ordered = ordered[[2, 3, 0, 1]]

    return ordered.astype(np.float32)


def unwrap_strip(bgr: np.ndarray, quad: np.ndarray) -> np.ndarray:
    corners = _order_corners(np.asarray(quad, dtype=np.float32))

    long_side = max(
        np.linalg.norm(corners[1] - corners[0]),
        np.linalg.norm(corners[2] - corners[3]),
    )
    short_side = max(
        np.linalg.norm(corners[3] - corners[0]),
        np.linalg.norm(corners[2] - corners[1]),
    )

    width = UNWRAP_WIDTH
    height = int(np.clip(width * short_side / max(long_side, 1e-6), 40, UNWRAP_MAX_HEIGHT))

    destination = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(corners, destination)
    return cv2.warpPerspective(bgr, matrix, (width, height), flags=cv2.INTER_LINEAR)


def sample_pads(
    strip: np.ndarray,
    pad_count: int,
    pad_start: float = 0.0,
    pad_end: float = 1.0,
) -> np.ndarray:
    height, width = strip.shape[:2]

    band_start = int(np.clip(pad_start, 0.0, 0.99) * width)
    band_end = int(np.clip(pad_end, 0.01, 1.0) * width)
    band_end = max(band_end, band_start + 1)
    cell_width = (band_end - band_start) / pad_count

    colours = np.zeros((pad_count, 3), dtype=np.float64)
    for index in range(pad_count):
        x0 = int(band_start + index * cell_width + 0.25 * cell_width)
        x1 = int(band_start + (index + 1) * cell_width - 0.25 * cell_width)
        y0 = int(0.20 * height)
        y1 = int(0.80 * height)

        patch = strip[y0:y1, max(x0, 0) : max(x1, x0 + 1)]
        if patch.size == 0:
            patch = strip

        colours[index] = np.median(patch.reshape(-1, 3).astype(np.float64), axis=0)

    return colours


def white_balance(colours: np.ndarray, strip: np.ndarray) -> tuple[np.ndarray, bool]:
    pixels = strip.reshape(-1, 3).astype(np.float32)
    hsv = cv2.cvtColor(strip, cv2.COLOR_BGR2HSV).reshape(-1, 3)

    bright = hsv[:, 2] >= np.percentile(hsv[:, 2], 90)
    neutral = hsv[:, 1] <= np.percentile(hsv[:, 1], 50)
    reference_pixels = pixels[bright & neutral]
    if reference_pixels.shape[0] < 20:
        return colours, False

    reference = np.median(reference_pixels, axis=0)
    if np.any(reference < 30):
        return colours, False

    gain = np.clip(TARGET_WHITE / reference, 0.5, 2.0)
    return np.clip(colours * gain, 0, 255), True


def match_pads(colours: np.ndarray) -> list[PadReading]:
    readings: list[PadReading] = []

    for index, colour in enumerate(colours):
        spec = CHART[index % len(CHART)]
        bgr = np.clip(colour, 0, 255).astype(np.uint8)
        rgb = (int(bgr[2]), int(bgr[1]), int(bgr[0]))
        lab = rgb_to_lab(rgb)

        best_level = spec.levels[0]
        best_distance = float("inf")
        for level in spec.levels:
            distance = delta_e(lab, rgb_to_lab(level.rgb))
            if distance < best_distance:
                best_distance = distance
                best_level = level

        readings.append(
            PadReading(
                name=spec.name,
                value=best_level.label,
                abnormal=best_level.abnormal,
                delta_e=best_distance,
                rgb=rgb,
            )
        )

    return readings


def _annotate(bgr: np.ndarray, quad: np.ndarray, readings: list[PadReading]) -> np.ndarray:
    canvas = bgr.copy()
    corners = _order_corners(np.asarray(quad, dtype=np.float32)).astype(np.int32)

    cv2.polylines(canvas, [corners], True, (0, 200, 0), 3)
    cv2.circle(canvas, tuple(corners[0]), 7, (0, 165, 255), -1)

    bar_height = 46
    bar = np.full((bar_height, canvas.shape[1], 3), 30, np.uint8)
    slot = canvas.shape[1] // max(len(readings), 1)
    for index, reading in enumerate(readings):
        x0 = index * slot
        bar[:, x0 : x0 + slot - 4] = (reading.rgb[2], reading.rgb[1], reading.rgb[0])

    return np.vstack([canvas, bar])


def analyze(
    bgr: np.ndarray,
    pad_count: int = len(CHART),
    calibrate: bool = True,
    quad: np.ndarray | None = None,
    pad_start: float = 0.0,
    pad_end: float = 1.0,
) -> StripResult:
    if bgr is None or bgr.size == 0:
        return StripResult(ok=False, message="Empty image.")

    if quad is None:
        detected = find_strip(bgr)
        if detected is None:
            return StripResult(
                ok=False,
                message=(
                    "No strip found. Put it on a plain, contrasting background, fill "
                    "the frame and try again, or switch on manual mode."
                ),
            )
        quad = detected

    strip = unwrap_strip(bgr, quad)
    colours = sample_pads(strip, pad_count, pad_start, pad_end)

    calibrated = False
    if calibrate:
        colours, calibrated = white_balance(colours, strip)

    readings = match_pads(colours)

    return StripResult(
        ok=True,
        readings=readings,
        quad=np.asarray(quad, dtype=np.float32),
        unwrapped=strip,
        annotated=_annotate(bgr, quad, readings),
        calibrated=calibrated,
    )


def manual_quad(
    shape: tuple[int, ...],
    angle: float,
    cx: float,
    cy: float,
    length: float,
    thickness: float,
) -> np.ndarray:
    height, width = shape[:2]
    centre = np.array([cx * width, cy * height])
    half_length = 0.5 * length * width
    half_thickness = 0.5 * thickness * height

    theta = np.deg2rad(angle)
    along = np.array([np.cos(theta), np.sin(theta)])
    across = np.array([-np.sin(theta), np.cos(theta)])

    return np.array(
        [
            centre - half_length * along - half_thickness * across,
            centre + half_length * along - half_thickness * across,
            centre + half_length * along + half_thickness * across,
            centre - half_length * along + half_thickness * across,
        ],
        dtype=np.float32,
    )


def demo_strip(
    pad_count: int = len(CHART),
    angle: float = 6.0,
    background: tuple[int, int, int] = (48, 58, 52),
) -> np.ndarray:
    height, width = 520, 900
    canvas = np.full((height, width, 3), background, np.uint8)

    strip_w, strip_h = 700, 110
    strip = np.full((strip_h, strip_w, 3), 250, np.uint8)

    handle = int(strip_w * DEMO_PAD_START)
    cell = (strip_w - handle) / pad_count

    rng = np.random.default_rng(7)
    for index in range(pad_count):
        spec = CHART[index % len(CHART)]
        level = spec.levels[DEMO_PLAN[index % len(DEMO_PLAN)] % len(spec.levels)]
        colour = np.array(level.rgb[::-1], np.float64) + rng.normal(0, 3, 3)

        x0 = int(handle + index * cell + 0.12 * cell)
        x1 = int(handle + (index + 1) * cell - 0.12 * cell)
        strip[14 : strip_h - 14, x0:x1] = np.clip(colour, 0, 255).astype(np.uint8)

    matrix = cv2.getRotationMatrix2D((strip_w / 2, strip_h / 2), angle, 1.0)
    matrix[0, 2] += (width - strip_w) / 2
    matrix[1, 2] += (height - strip_h) / 2

    rotated = cv2.warpAffine(strip, matrix, (width, height), borderValue=background)
    mask = cv2.warpAffine(
        np.full((strip_h, strip_w), 255, np.uint8), matrix, (width, height)
    )
    canvas[mask > 0] = rotated[mask > 0]
    return canvas


def selftest() -> int:
    result = analyze(demo_strip(), pad_start=DEMO_PAD_START)
    if not result.ok:
        print(f"FAIL: {result.message}")
        return 1

    expected = [
        spec.levels[DEMO_PLAN[index] % len(spec.levels)].label
        for index, spec in enumerate(CHART)
    ]

    failures = 0
    for reading, want in zip(result.readings, expected):
        passed = reading.value == want
        failures += 0 if passed else 1
        print(
            f"  {'PASS' if passed else 'FAIL'}  {reading.name:<12} "
            f"read={reading.value:<9} expected={want:<9} dE={reading.delta_e:5.1f}"
        )

    print(f"\n{len(expected) - failures}/{len(expected)} pads read correctly")
    return 1 if failures else 0


def _main() -> None:
    import sys
    from pathlib import Path

    if len(sys.argv) >= 2 and sys.argv[1] in {"--selftest", "selftest"}:
        raise SystemExit(selftest())

    if len(sys.argv) >= 2 and sys.argv[1] in {"--demo", "demo"}:
        image = demo_strip()
        source = "synthetic demo strip"
        pad_start = DEMO_PAD_START
    elif len(sys.argv) < 2:
        print("usage: python strip_analyzer.py <image.jpg> [output.jpg]")
        print("       python strip_analyzer.py demo")
        print("       python strip_analyzer.py selftest")
        raise SystemExit(1)
    else:
        path = Path(sys.argv[1])
        image = cv2.imread(str(path))
        if image is None:
            print(f"could not read {path}")
            raise SystemExit(1)
        source = str(path)
        pad_start = 0.0

    result = analyze(image, pad_start=pad_start)
    if not result.ok:
        print(f"failed: {result.message}")
        raise SystemExit(1)

    print(f"source     : {source}")
    print(f"calibrated : {'yes' if result.calibrated else 'no'}")
    print()
    for reading in result.readings:
        flag = "out of range" if reading.abnormal else "in range"
        print(
            f"  {reading.name:<12} {reading.value:<9} {flag:<12} "
            f"dE={reading.delta_e:5.1f} ({reading.confidence})"
        )

    targets = [a for a in sys.argv[2:] if not a.startswith("-")]
    out = Path(targets[0]) if targets else Path("strip_annotated.jpg")
    cv2.imwrite(str(out), result.annotated)
    if result.unwrapped is not None:
        cv2.imwrite(str(out.with_name(out.stem + "_flat.jpg")), result.unwrapped)
    print(f"\nwrote      : {out}")


if __name__ == "__main__":
    _main()
