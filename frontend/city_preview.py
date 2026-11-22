from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="CivicPulse AI - 3D Smart City",
    page_icon="🏙️",
    layout="wide"
)

st.title("🏙️ CivicPulse AI")
st.subheader("Interactive 3D Smart City Preview")

html_path = Path(__file__).with_name("smart_city.html")

if html_path.exists():
    html_content = html_path.read_text(encoding="utf-8")

    components.html(
        html_content,
        height=650,
        scrolling=False
    )
else:
    st.error("smart_city.html was not found in the frontend folder.")