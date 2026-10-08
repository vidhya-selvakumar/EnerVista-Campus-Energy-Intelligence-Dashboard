from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSS_FILE = PROJECT_ROOT / "assets" / "styles.css"


def load_global_styles() -> None:
    """Load the shared EnerVista theme for every Streamlit page."""

    if not CSS_FILE.exists():
        return

    css = CSS_FILE.read_text(encoding="utf-8")
    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )