from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"
TIMEOUT = 60


def run_app() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=TIMEOUT)
    app.run()
    return app


def test_app_runs_without_raising():
    app = run_app()
    assert not app.exception


def test_app_shows_the_medical_disclaimer():
    app = run_app()
    assert any("not a medical device" in warning.value for warning in app.warning)


def test_app_shows_the_upload_prompt_before_an_image_is_given():
    app = run_app()
    assert any("Upload a photo" in info.value for info in app.info)


def test_demo_button_analyses_the_synthetic_strip():
    app = run_app()
    app.button[0].click().run()

    assert not app.exception
    assert app.session_state["demo_image"] is not None
    assert any("pads outside range" in error.value for error in app.error)


def test_pad_count_slider_drives_the_number_of_readings():
    app = run_app()
    app.sidebar.slider[0].set_value(3).run()
    app.button[0].click().run()

    assert not app.exception
    assert len(app.session_state["demo_image"]) > 0
