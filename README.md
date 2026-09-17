# Test Strip Reader

Reads the pad colours on a urine test strip from a photo using classical computer
vision: strip detection, perspective correction, per-pad colour sampling, white
balance, and CIE-Lab colour matching against a reference chart. No machine learning.

Educational demo, not a medical device. This reads the colours on a strip; it does
not perform the chemistry and cannot diagnose anything. Follow the instructions
supplied with your strips and confirm any result with a clinician.

Tested only on a synthetic strip. Accuracy on a real strip is unknown.

![Example output](docs/example.jpg)

The synthetic demo strip. The green quad is the detected strip; the bar along the
bottom is the colour measured for each pad.

## Features

- Detects one strip in a photo against a plain background, then rectifies rotation
  and perspective into a fixed width strip image
- Samples each pad by median from the middle of its cell, so glare and bleed do not
  drag the colour
- Estimates the lighting cast from neutral bright pixels inside the strip and scales
  the channels to remove it
- Classifies every pad against the reference chart in CIE-Lab by delta-E, and flags
  levels outside the normal range
- Reports the match distance per pad, so an unreadable strip can be spotted
- Manual strip region, adjustable pad count and pad band for strips that auto
  detection cannot handle
- Export to CSV, an annotated overlay, and the straightened strip that was sampled
- A seeded synthetic strip generator, which makes the whole pipeline testable
  without a camera or a physical strip
- Browser interface and command line interface over the same pipeline

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

- **Median, not mean**, for the pad colour. One specular highlight drags a mean badly.
- **Lab, not RGB.** Distance in Lab approximates perceived colour difference; distance
  in RGB does not.
- **delta-E is reported as a match distance, not as confidence.** It says how close the
  measured colour is to the nearest chart colour and nothing more. A high value may mean
  glare, blur or shadow, but a low value does not confirm the reading is correct, because
  a poor white balance can shift every pad and still land close to the wrong level.

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

**Replace the chart.** `CHART` in `strip_reader/chart.py` is made-up start-up data, not
colours taken from any real product. Every manufacturer prints different colours. This
is the single biggest source of error and it is about ten lines to fix.

**Set the pad region.** Most dipsticks have a white handle. If the sampling grid
lands on it, the first pads read as false negatives. Move "Pads start at" in the
sidebar until the cells line up with the coloured squares in the straightened view.

**Validate it.** Read a real strip by eye against the packaging chart, write down the
answers, then run it through the tool and build a confusion matrix. Report that
number rather than claiming the tool works.

## Limitations

- Auto-detection needs a plain, contrasting background. Manual mode otherwise.
- Colour depends on lighting, camera white balance and screen calibration.
- The tool cannot know how long a strip has been developing. Most are read at 60 or
  120 seconds, and a photo taken at the wrong time is simply wrong.
- Pads bleed into each other on cheap strips. Only the middle 50% of each cell is
  sampled.
- Blood and leukocytes are non-specific. Menstruation, discharge and dehydration all
  affect them.

## License

MIT
