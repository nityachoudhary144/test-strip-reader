# Test Strip Reader

Uses classical computer vision to read the colors on a urine test strip from a photo: strip detection, correction for perspective distortion, color sampling for each pad, white balance, and matching to a reference color chart using CIE-Lab color matching. No machine learning.

Educational demonstration, not a diagnostic device. Reads the colors on a strip,
does no chemistry, and cannot diagnose anything. Follow instructions supplied with
your strips and get any diagnosis verified by a clinician.

Only tested on a simulated strip. Accuracy on an actual strip is unknown.
![Example output](docs/example.jpg)

The synthetic demo strip. The green quad is the detected strip; the bar along the
bottom is the colour measured for each pad.

## Features

- Detects a single strip in an image on a homogeneous background, and corrects
  the strip orientation and perspective to get a fixed-width strip image
- Extracts the color of each pad by sampling the median of its cell in the middle,
  thus eliminating effects like glare and bleed
- Compensates for lighting effects based on the neutral pixels of the strip,
  and scales the channels to eliminate it
- Compares each pad with the reference chart in CIE-Lab using delta-E measure,
  and marks any out-of-range values
- Returns the comparison value for each pad, thus allowing for the identification
  of unreadable strip
- Manual detection of strip region, custom number of pads and pad bands in case
  of strips which are impossible to automatically detect
- Exports results to CSV file, annotated overlay image, and straightened strip image
  which was used for sampling
- An automated strip generation utility, allowing to test the pipeline without
  actual hardware
- Web-based interface and CLI interface on top of the pipeline
## Project documentation

| File | Contents |
| --- | --- |
| `statement.md` | Problem statement, scope, target users, high level features |
| `docs/design.md` | Requirements, architecture, UML diagrams, design decisions, evaluation method |
| `docs/diagrams/` | Diagram images rendered from the Mermaid sources in `docs/design.md` |

## Technologies

Python 3.13, OpenCV, NumPy, Streamlit and Pillow at run time. pytest for the test
suite. Diagrams are written in Mermaid, which GitHub renders in place, and rendered
to images by `docs/build_diagrams.py` for anything that cannot read Mermaid.
No machine learning framework is used and no model weights are downloaded.

## Pipeline

```
photo
  locate strip      background differencing, minAreaRect on the largest
                    elongated contour
  straighten        order corners, getPerspectiveTransform, warpPerspective
  sample pads       median colour from the centre of each of N cells
  white balance     scale channels so the strip's white area reads neutral
  match             nearest chart colour in CIE-Lab by delta-E
```

Three implementation choices:

- Use **median, not mean**, to calculate pad color. Specular highlights skew a mean.
- **Lab color space, not RGB.** Distance between colors in Lab is an estimate of
  perceptual color difference; distance between colors in RGB is not.
- **Report delta-E as a match distance, not as a measure of confidence.** It is the
  distance between the measured color and the nearest color on the chart. Delta-E
  being high may indicate glare, blur, or shadow; delta-E being low does not indicate
  correct reading because poor white balance will move all pads to a similar level,
  even though it is incorrect.
## Files

| Path | Purpose |
| --- | --- |
| `strip_reader/chart.py` | Reference chart: `Level`, `PadSpec`, `CHART` |
| `strip_reader/colour.py` | CIE-Lab conversion, delta-E, white balance |
| `strip_reader/detect.py` | Strip detection, corner ordering, rectification, manual quad |
| `strip_reader/sample.py` | Per-pad median sampling |
| `strip_reader/match.py` | Nearest level classification, `PadReading`, confidence bands |
| `strip_reader/annotate.py` | Overlay and swatch bar rendering |
| `strip_reader/analyzer.py` | `analyze`, `StripResult`, stage orchestration |
| `strip_reader/synthetic.py` | Synthetic demo strip and its expected labels |
| `strip_reader/export.py` | CSV, annotated image and flat strip writers |
| `strip_reader/cli.py` | Command line interface |
| `app.py` | Streamlit UI |
| `tests/` | pytest suite |
| `samples/` | Drop your own photos here. Gitignored. |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Browser interface:

```bash
streamlit run app.py
```

Command line:

```bash
python -m strip_reader.cli demo                     # synthetic strip, no photo needed
python -m strip_reader.cli selftest                 # verify the pipeline
python -m strip_reader.cli analyze samples/mine.jpg # your own photo
```

`demo` and `analyze` accept `--pads`, `--pad-start`, `--pad-end`, `--no-calibrate`,
`--output` and `--csv`. Run `python -m strip_reader.cli analyze --help` for the full
list.

`selftest` renders the demo strip, checks that all six pads read back correctly, and
exits non-zero on any mismatch.

`demo` and a run on your own photo both write `strip_annotated.jpg` (overlay) and
`strip_annotated_flat.jpg` (the straightened strip that actually gets sampled, which
is the useful one when debugging a bad reading).

## Testing

```bash
pytest
```

The suite covers the colour conversions and the calibration fallback, the geometry
and corner ordering, pad sampling including a specular highlight, the classification
and its confidence bands, the CSV and image writers, and the synthetic generator. It
also runs the full pipeline end to end and asserts that every pad on the demo strip
reads back as the level the generator painted, which is the same check `selftest`
makes.

The interface is covered as well. The tests drive the Streamlit app through
Streamlit's own test harness, run the demo path, and check that the disclaimer, the
upload prompt and the out of range summary all render.

The suite needs no camera, no sample photo and no network, because the fixture is
generated from a fixed seed.

## Before trusting a reading

**Replace the chart.** `CHART` in `strip_reader/chart.py` is artificial start-up data, but
not colours derived from any actual device. Each manufacturer has unique colours. This
is the largest single source of errors and will be corrected in about ten lines.

**Set pad region.** Most dipsticks come with white handles. When the sampling grid
falls onto the handle, the initial pads turn into false negatives. Change "Pads start at"
in the sidebar so that the cells correspond to the coloured boxes in the flattened
view.

**Validate it.** Look at an actual strip with your own eyes compared to the chart in
the packaging, write down the values, and then test them using the tool and create
confusion matrix. Provide this value rather than saying the tool works perfectly.
## Limitations

- Auto-detection requires a clear, contrasting background; otherwise, go manual.
- Coloration is dependent on lighting, camera white balance, and screen calibration.
- Time for development cannot be measured by the software; most strips are usually read
  after 60 and 120 seconds. If the picture is taken too early or late, it is wrong.
- Cheaper strips have cells that run into each other; only 50% of the middle of each
  cell is used.
- Blood and leukocytes are not specific; they are affected by menstruation,
  discharge, and dehydration.
## License

MIT
