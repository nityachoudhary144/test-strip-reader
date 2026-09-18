# Statement

## Problem statement

The result of testing by a urine dipstick involves comparing the colour on the test
strip to a chart printed on the packaging. The test is conducted based on room light,
the amount of development time, and eyesight of the person reading the results.
Two different people will read the same test strip differently. Reading the result
under a colour bias or from a photo which had glare will give incorrect results
without anyone being aware of the error.

By taking a picture of the test strip, some of the variability is addressed because
the image can be corrected using the numerical values. However, taking a photo
of the same test strip will not yield the same results because a camera records the
lighting conditions. It becomes even harder when attempting to compare the colours
of pads by viewing the chart on the computer screen.
This particular project sees the photo as an instrument of measurement. The project will find the location of the strip, adjust for perspective, sample the pads, eliminate the lighting shadows, and report the closest color on the chart along with the distance between the two colors.

The subject area of this project is computer vision, and this is an example of a vision problem start to finish: image capture, color space transformation, noise filtering, geometry correction, segmentation, and classification against a reference. No machine learning is involved because the printed reference chart is, after all, a classifier.

## Objectives

1. Find a strip in a regular photograph and correct the perspective automatically,
   so that the measurement is independent of how the strip was placed.
2. Determine the colour of each pad in numbers, which would not depend on changes in
   the lighting conditions, applying the white balance procedure triggered by the strip.
3. Compare each measurement to a chart printed in a perceptually uniform colour space,
   and indicate the quality of the match, instead of reporting just the level.
4. Be honest about the uncertainty, marking the poorly-matched measurement
   instead of reporting everything as equally reliable.
5. Ensure that the reference chart is replacable, so that the tool could
   be applied to a real product through data editing.
6. Check the pipeline without the physical strip, so that the geometry and colour
   mathematics could be verified repeatedly and deterministically.
## Scope

In scope:

Scope:

- Identifying the presence of one strip in a still image taken against a simple background
- Compensating for any rotation and perspective to align the strip with the axes
- Capturing the color of each pad from the center of its cell
- Estimating and neutralizing the effect of illumination through a grey world correction
- Classifying each pad in relation to a user customizable chart in CIE-Lab space
- Returning a measure of the match for each pad and indicating when the levels fall outside the normal range
- Saving the results as a CSV file and an annotated image
- A web interface and a CLI interface using the same processing pipeline
- A test suite automatically exercising the geometric, color sampling and color classification steps

Out of scope:

- Any claim about the clinical relevance of the test. This device measures colours, not diagnoses.
- Timing the development of the strip. This device does not know when the photo was taken.
- Multiple strip images, hand-held strips, and strong background textures
- Mobile testing, video, and any on-device processing
- Results storage/sharing, since a result is a single measurement
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
1. Strip detection and correction. The background is separated using background
   differencing, the strip contour is detected and reduced to a rotated rectangle,
   corner ordering and a perspective transform create a strip of fixed width and
   axis alignment. Manual detection is performed when the background is crowded.

2. Pad sampling and correction. For each of the N pads, a sample is created using
   the median value of the pixel located at the center of the cell, and not
   belonging to the edges where pads overlap. Bright low saturation pixels located
   within the strip are considered white references and used for scaling.

3. Classification and output. For each sample the RGB values are transformed into
   CIE-Lab space and then compared against levels defined by reference chart using
   delta-E metric. The output consists of the level name, if it is out-of-bound,
   delta-E distance and confidence interval.
   
5. Two interfaces over one pipeline. A Streamlit app for interactive use with an
   uploaded photo or a generated demo strip, and a command line tool with
   `demo`, `analyze` and `selftest` subcommands.

6. A synthetic strip generator. Renders a strip from the reference chart at a chosen
   angle, which makes the pipeline testable without a physical strip or a camera and
   gives the test suite a known ground truth.
