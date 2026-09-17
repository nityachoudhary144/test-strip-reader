from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from strip_reader.analyzer import StripResult, analyze
from strip_reader.chart import CHART
from strip_reader.export import write_csv, write_result
from strip_reader.synthetic import DEMO_PAD_START, demo_strip, expected_labels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="strip_reader",
        description="Read the pad colours on a urine test strip from a photo.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    demo = commands.add_parser("demo", help="analyse a synthetic strip")
    demo.add_argument("--pads", type=int, default=len(CHART))
    demo.add_argument("--angle", type=float, default=6.0)
    demo.add_argument("--output", default="strip_annotated.jpg")
    demo.add_argument("--csv")

    analyse = commands.add_parser("analyze", help="analyse a photo of a strip")
    analyse.add_argument("image")
    analyse.add_argument("--pads", type=int, default=len(CHART))
    analyse.add_argument("--pad-start", type=float, default=0.0)
    analyse.add_argument("--pad-end", type=float, default=1.0)
    analyse.add_argument("--no-calibrate", action="store_true")
    analyse.add_argument("--output", default="strip_annotated.jpg")
    analyse.add_argument("--csv")

    commands.add_parser("selftest", help="check the pipeline against a synthetic strip")
    return parser


def report(result: StripResult, source: str) -> None:
    print(f"source     : {source}")
    print(f"calibrated : {'yes' if result.calibrated else 'no'}")
    print()
    for reading in result.readings:
        flag = "out of range" if reading.abnormal else "in range"
        print(
            f"  {reading.name:<12} {reading.value:<9} {flag:<12} "
            f"dE={reading.delta_e:5.1f} ({reading.confidence})"
        )


def selftest(pad_count: int = len(CHART)) -> int:
    result = analyze(
        demo_strip(pad_count=pad_count),
        pad_count=pad_count,
        pad_start=DEMO_PAD_START,
    )
    if not result.ok:
        print(f"FAIL: {result.message}")
        return 1

    expected = expected_labels(pad_count)
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "selftest":
        return selftest()

    if args.command == "demo":
        image = demo_strip(pad_count=args.pads, angle=args.angle)
        source = "synthetic demo strip"
        result = analyze(image, pad_count=args.pads, pad_start=DEMO_PAD_START)
    else:
        path = Path(args.image)
        image = cv2.imread(str(path))
        if image is None:
            print(f"could not read {path}")
            return 1
        source = str(path)
        result = analyze(
            image,
            pad_count=args.pads,
            calibrate=not args.no_calibrate,
            pad_start=args.pad_start,
            pad_end=args.pad_end,
        )

    if not result.ok:
        print(f"failed: {result.message}")
        return 1

    report(result, source)

    out, flat = write_result(result, args.output)
    print(f"\nwrote      : {out}")
    if flat is not None:
        print(f"wrote      : {flat}")
    if args.csv:
        print(f"wrote      : {write_csv(result, args.csv)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
