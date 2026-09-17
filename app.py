from __future__ import annotations

import cv2
import numpy as np
import streamlit as st
from PIL import Image

import strip_reader as sr

st.set_page_config(page_title="Test Strip Reader", layout="wide")

DISCLAIMER = (
    "Educational demo, not a medical device. This reads the colours on a test strip. "
    "It does not perform the chemistry and cannot diagnose anything. Use the "
    "instructions supplied with your strips and confirm any result with a clinician."
)


def to_bgr(pil_image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)


def to_rgb(bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def show_results(result: sr.StripResult) -> None:
    if not result.ok:
        st.error(result.message)
        return

    left, right = st.columns([3, 2])

    with left:
        st.image(to_rgb(result.annotated), caption="Detected strip", width="stretch")
        if result.unwrapped is not None:
            st.image(
                to_rgb(result.unwrapped),
                caption="Straightened strip, the image that gets sampled",
                width="stretch",
            )

    with right:
        if result.abnormal:
            st.error(f"{len(result.abnormal)} of {len(result.readings)} pads outside range")
        else:
            st.success("All pads within range")

        if not result.calibrated:
            st.warning("White balance skipped, colours may carry a lighting cast.")

        st.divider()
        for reading in result.readings:
            status = "out of range" if reading.abnormal else "in range"
            st.markdown(
                f"**{reading.name}** &nbsp; `{reading.value}` &nbsp; {status}  \n"
                f"<span style='opacity:0.7;font-size:0.85em'>"
                f"delta-E {reading.delta_e:.1f}, {reading.confidence} match</span>",
                unsafe_allow_html=True,
            )

        st.divider()
        st.image(to_rgb(sr.swatch_strip(result.readings)), caption="Measured colours")

        if result.poor_matches:
            st.warning(
                "Some pads matched poorly (delta-E above 15). That may mean blur, "
                "glare or a shadow across the strip."
            )

        st.download_button(
            "Download readings as CSV",
            sr.readings_to_csv(result),
            file_name="strip_readings.csv",
            mime="text/csv",
        )


def sidebar_controls():
    st.sidebar.header("Settings")

    pad_count = st.sidebar.slider(
        "Pads on the strip",
        min_value=1,
        max_value=12,
        value=len(sr.CHART),
    )
    calibrate = st.sidebar.checkbox("White balance", value=True)

    pad_start = st.sidebar.slider("Pads start at", 0.0, 0.6, 0.0, 0.01)
    pad_end = st.sidebar.slider("Pads end at", 0.4, 1.0, 1.0, 0.01)

    st.sidebar.divider()
    manual = st.sidebar.checkbox("Manual mode", value=False)

    layout = {"angle": 0.0, "cx": 0.5, "cy": 0.5, "length": 0.8, "thickness": 0.22}
    if manual:
        layout["angle"] = st.sidebar.slider("Rotation", -45.0, 45.0, 0.0, 0.5)
        layout["cx"] = st.sidebar.slider("Centre X", 0.1, 0.9, 0.5, 0.01)
        layout["cy"] = st.sidebar.slider("Centre Y", 0.1, 0.9, 0.5, 0.01)
        layout["length"] = st.sidebar.slider("Length", 0.2, 1.0, 0.8, 0.01)
        layout["thickness"] = st.sidebar.slider("Thickness", 0.05, 0.8, 0.22, 0.01)

    return pad_count, calibrate, manual, layout, pad_start, pad_end


st.title("Test Strip Reader")
st.caption("Estimates the pad colours on a urine test strip from a photo")
st.warning(DISCLAIMER)

pad_count, calibrate, manual, layout, pad_start, pad_end = sidebar_controls()

tab_upload, tab_demo, tab_method = st.tabs(["Upload a photo", "Demo strip", "Method"])

with tab_upload:
    uploaded = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded is not None:
        image = to_bgr(Image.open(uploaded))
        quad = sr.manual_quad(image.shape, **layout) if manual else None
        show_results(
            sr.analyze(
                image,
                pad_count=pad_count,
                calibrate=calibrate,
                quad=quad,
                pad_start=pad_start,
                pad_end=pad_end,
            )
        )
    else:
        st.info("Upload a photo of a strip on a plain background, or use the demo tab.")

with tab_demo:
    st.write(
        "Renders a synthetic strip so the pipeline can be run without a physical strip. "
        "The colours are illustrative, so this exercises the geometry and colour "
        "matching rather than measuring anything."
    )
    angle = st.slider("Rotation", -25.0, 25.0, 6.0, 0.5)

    if st.button("Analyse demo strip", type="primary"):
        st.session_state["demo_image"] = sr.demo_strip(pad_count=pad_count, angle=angle)

    stored = st.session_state.get("demo_image")
    if stored is not None:
        show_results(
            sr.analyze(
                stored,
                pad_count=pad_count,
                calibrate=calibrate,
                pad_start=sr.DEMO_PAD_START,
            )
        )

with tab_method:
    st.markdown(
        """
```
photo
  locate strip      background differencing, minAreaRect on the largest
                    elongated contour
  straighten        order corners, getPerspectiveTransform, warpPerspective
  sample pads       median colour from the centre of each of N cells
  white balance     scale channels so the strip's white area reads neutral
  match             nearest chart colour in CIE-Lab by delta-E
```

Median rather than mean, so one specular highlight cannot drag a pad colour. Lab
rather than RGB, because distance in Lab approximates perceived colour difference
and distance in RGB does not. The delta-E figure is a match distance, not a
confidence. It says how close the measured colour is to the nearest chart colour. A
high value may mean glare, blur or shadow, but a low value does not confirm the
reading is correct.

Two things to set before trusting a reading. The chart in `strip_reader/chart.py` is
made-up start-up data, not colours taken from a real product, and should be replaced
with the colours printed on your own strip's packaging. A strip with a handle also
needs "Pads start at" moved until the cells line up with the coloured squares in the
straightened view, otherwise the first pads land on blank plastic and read as false
negatives.

So far this has only been run on a synthetic strip. Accuracy on a real strip is
unknown.
        """
    )
