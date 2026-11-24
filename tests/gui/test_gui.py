"""Small GUI contract; scenario-specific checks are added during the exercise."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT/'calculator/gui/app.py'
if not APP.is_file():
    pytest.skip('Seminar start: Streamlit GUI has not been implemented.', allow_module_level=True)


def test_calculate_and_display():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    calculate = [button for button in app.button if button.label == 'Calculate']
    assert len(calculate) == 1
    calculate[0].click().run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 4
    assert len(app.dataframe) >= 1
    assert any('download_button' in str(node.type) for node in app)
