from __future__ import annotations

import csv
import io

from strip_reader.analyzer import analyze
from strip_reader.chart import CHART
from strip_reader.export import CSV_FIELDS, readings_to_csv, write_csv, write_result
from strip_reader.synthetic import DEMO_PAD_START, demo_strip


def analysed_demo():
    return analyze(demo_strip(), pad_start=DEMO_PAD_START)


def test_csv_has_one_row_per_pad_plus_a_header():
    rows = list(csv.reader(io.StringIO(readings_to_csv(analysed_demo()))))
    assert rows[0] == list(CSV_FIELDS)
    assert len(rows) == len(CHART) + 1


def test_csv_carries_the_reading_values():
    rows = list(csv.reader(io.StringIO(readings_to_csv(analysed_demo()))))
    names = [row[0] for row in rows[1:]]
    assert names == [spec.name for spec in CHART]
    assert all(row[2] in {"in range", "out of range"} for row in rows[1:])


def test_write_result_creates_the_overlay_and_the_flat_strip(tmp_path):
    out, flat = write_result(analysed_demo(), tmp_path / "run.jpg")
    assert out.exists()
    assert flat is not None and flat.exists()
    assert flat.name == "run_flat.jpg"


def test_write_csv_creates_the_file(tmp_path):
    target = write_csv(analysed_demo(), tmp_path / "readings.csv")
    assert target.exists()
    assert target.read_text(encoding="utf-8").startswith("pad,value,status")


def test_write_result_makes_missing_directories(tmp_path):
    out, _ = write_result(analysed_demo(), tmp_path / "nested" / "deep" / "run.jpg")
    assert out.exists()
