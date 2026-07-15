from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="CIS README",
    page_icon="📖",
    layout="wide",
)

# Keep the default Streamlit multipage navigation and enlarge its font only.
st.markdown(
    """
    <style>
    div[data-testid="stSidebarNav"] a,
    div[data-testid="stSidebarNav"] span,
    div[data-testid="stSidebarNav"] p {
        font-size: 22px !important;
    }

    .main .block-container {
        max-width: 1100px;
        padding-top: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

README_PATH = Path(__file__).resolve().parents[1] / "README.md"

st.title("📖 CIS README")
st.caption("Coffee Intelligence System • Project Overview & Release Notes")
st.divider()

if README_PATH.exists():
    try:
        readme_text = README_PATH.read_text(encoding="utf-8")
        st.markdown(readme_text)
    except Exception as exc:
        st.error(f"README.md gagal dibaca: {exc}")
else:
    st.warning(
        "README.md belum ditemukan di folder utama repository. "
        "Letakkan README.md sejajar dengan app.py."
    )
