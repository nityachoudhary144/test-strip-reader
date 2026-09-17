# Statement

## Problem statement

A urine dipstick is read by holding the strip against the colour chart printed on
the packaging and matching each pad by eye, at a fixed development time. The
comparison depends on the light in the room, on how long the strip has been
developing, and on the eyesight of the person holding it. Two people can read the
same strip differently, and a reading taken under a colour cast or from a photo
with glare can be wrong without anyone realising it.

A photograph of the strip removes some of that variability, because the image can
be corrected and measured numerically. It also introduces a new problem: a camera
records whatever the lighting was, so two photos of the same strip rarely produce
the same numbers. Comparing pad colours by eye against a chart on a screen is
worse still, because the display is calibrated differently again.

This project treats the photograph as a measurement. It locates the strip,
corrects its perspective, samples each pad, removes the lighting cast, and reports
the nearest colour on the reference chart together with a distance that says how
close the match was.

The subject matter is computer vision, and this is a vision problem end to end:
image acquisition, colour space conversion, noise rejection, geometric
rectification, segmentation and classification against a reference. No machine
learning is used, because a printed reference chart is already a labelled
classifier; the work is in reading it reliably.

## Scope

In scope:

- Detecting a single strip in a still photograph against a plain background
- Correcting rotation and perspective so the strip is axis aligned
- Sampling the colour of each pad from the centre of its cell
- Estimating and removing the lighting cast with a grey world style correction
- Classifying each pad against a user replaceable reference chart in CIE-Lab
- Reporting a match distance per pad and flagging levels outside the normal range
- Exporting the measurements as CSV and an annotated image
- A browser interface and a command line interface over the same pipeline
- An automated test suite covering the geometry, sampling, colour and output stages

Out of scope:

- Any claim of clinical validity. The tool reports colours, not diagnoses.
- Timing the development of the strip. The tool cannot know when the photo was taken.
- Multi strip images, strips held in a hand, or backgrounds with strong texture
- Mobile capture, video, and any on device inference
- Storage or sharing of results, because a reading is a single ephemeral measurement

## Target users

- A student or demonstrator running the pipeline on a sample photo to see the
  geometry and colour stages working on real pixels
- Anyone wanting to know whether a photographed strip is readable at all, judged by
  the delta-E distances, before trusting the levels
- A developer replacing the reference chart with the real colours from a specific
  product, which is a roughly ten line change in one file

The tool is explicitly not aimed at patients, and the interface says so on every
screen.

## High level features

1. Strip detection and rectification. Background differencing isolates the strip,
   the largest elongated contour is reduced to a rotated rectangle, its corners are
   ordered, and a perspective transform produces a fixed width, axis aligned strip
   image. A manual mode overrides detection when the background is cluttered.

2. Pad sampling and colour correction. Each of the N pad cells is sampled by median
   from the middle of the cell, avoiding the edges where pads bleed into each other.
   Bright, low saturation pixels inside the strip are taken as the white reference
   and used to scale the channels.

3. Classification and reporting. Every sampled colour is converted to CIE-Lab and
   matched to the nearest level on the reference chart by delta-E. The result carries
   the level, whether it is outside the normal range, the match distance, and a
   confidence band. Output is rendered as an overlay, a swatch bar, and CSV.

4. Two interfaces over one pipeline. A Streamlit app for interactive use with an
   uploaded photo or a generated demo strip, and a command line tool with
   `demo`, `analyze` and `selftest` subcommands.

5. A synthetic strip generator. Renders a strip from the reference chart at a chosen
   angle, which makes the pipeline testable without a physical strip or a camera and
   gives the test suite a known ground truth.
