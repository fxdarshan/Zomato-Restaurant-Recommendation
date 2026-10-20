"""Streamlit Host for Zomato AI Concierge Nocturne Gastronomy Frontend.

Renders the pixel-perfect Google Stitch dark luxury food-tech frontend
matching stitch_zomato_ai_dining_concierge:
- Authentic Tailwind Nocturne Palette (#0A0C10 canvas, #12151C midnight base, #181C26 elevated glass)
- Embedded SVG icons preventing any font-ligature overlapping
- Dark luxury pill buttons with glowing active states
- Constrained max-width layout (1440px)
- Interactive JavaScript communicating directly with the backend API
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Zomato Concierge — AI Dining Experience",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Strip Streamlit default padding, headers, footers and style iframe to full-bleed
st.markdown(
    """
    <style>
        /* Force dark background and remove Streamlit padding */
        .stApp {
            background-color: #111317 !important;
        }
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        header[data-testid="stHeader"] {
            display: none !important;
        }
        footer {
            display: none !important;
        }
        #MainMenu {
            visibility: hidden !important;
        }
        iframe {
            width: 100% !important;
            min-height: 2200px !important;
            border: none !important;
            background-color: #111317 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

frontend_file = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
if frontend_file.exists():
    html_code = frontend_file.read_text(encoding="utf-8")
    # Inside Streamlit iframe, route API calls directly to FastAPI on port 8000
    html_code = f"<script>window.API_BASE_URL = 'http://localhost:8000';</script>\n" + html_code
    st.components.v1.html(html_code, height=2200, scrolling=True)
else:
    st.error("Frontend template not found at frontend/index.html")
