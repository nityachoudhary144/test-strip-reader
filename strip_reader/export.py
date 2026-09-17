from __future__ import annotations

import csv
import io
from pathlib import Path

import cv2

from strip_reader.analyzer import StripResult

CSV_FIELDS = ("pad", "value", "status", "delta_e", "confidence", "r", "g", "b")


def readings_to_csv(result: StripResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_FIELDS)
    for reading in result.readings:
        writer.writerow(
            [
                reading.name,
                reading.value,
                "out of range" if reading.abnormal else "in range",
                f"{reading.delta_e:.2f}",
                reading.confidence,
                reading.rgb[0],
                reading.rgb[1],
                reading.rgb[2],
            ]
        )
    return buffer.getvalue()


def write_result(result: StripResult, path) -> tuple[Path, Path | None]:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), result.annotated)

    flat = None
    if result.unwrapped is not None:
        flat = out.with_name(out.stem + "_flat.jpg")
        cv2.imwrite(str(flat), result.unwrapped)

    return out, flat


def write_csv(result: StripResult, path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(readings_to_csv(result), encoding="utf-8")
    return out
