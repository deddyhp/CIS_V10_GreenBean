"""
Global CIS UI completion layer.

Loaded automatically by Python when the repository root is on sys.path.
It wraps Streamlit's set_page_config so every page receives the same
high-contrast futuristic green theme without changing database logic.
"""

try:
    import streamlit as st
except Exception:
    st = None

GLOBAL_CSS = r"""
<style>
:root {
    --cis-bg: #06110c;
    --cis-bg-soft: #0a1912;
    --cis-panel: #0d2118;
    --cis-panel-2: #10281d;
    --cis-border: rgba(92, 255, 174, 0.30);
    --cis-accent: #48f5a3;
    --cis-accent-soft: #95ffd0;
    --cis-text: #f2fff7;
    --cis-muted: #c7ddcf;
    --cis-muted-2: #a9c5b4;
}

/* Whole app */
.stApp {
    background:
        radial-gradient(circle at 85% 0%, rgba(72,245,163,.13), transparent 28%),
        radial-gradient(circle at 0% 100%, rgba(72,245,163,.08), transparent 25%),
        linear-gradient(180deg, var(--cis-bg), #04100a 100%) !important;
    color: var(--cis-text) !important;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07160f, #06110c) !important;
    border-right: 1px solid var(--cis-border) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--cis-text) !important;
}
section[data-testid="stSidebar"] a {
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] a:hover {
    background: rgba(72,245,163,.10) !important;
}

/* Main text contrast */
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMetricValue"] {
    color: var(--cis-text) !important;
}

p, li, label,
[data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"],
[data-testid="stWidgetLabel"],
small {
    color: var(--cis-muted) !important;
}

/* Inputs */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div,
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background: #f5f8f6 !important;
    color: #102019 !important;
    border-radius: 11px !important;
    border: 1px solid rgba(72,245,163,.25) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #66786d !important;
    opacity: 1 !important;
}

/* Select text and dropdown */
div[data-baseweb="select"] span,
div[data-baseweb="select"] input {
    color: #102019 !important;
}
ul[role="listbox"],
div[role="listbox"] {
    background: #f5f8f6 !important;
}
li[role="option"] {
    color: #102019 !important;
}

/* Buttons */
.stButton button,
.stFormSubmitButton button,
button[kind="primary"] {
    border-radius: 12px !important;
    border: 1px solid var(--cis-border) !important;
    background: linear-gradient(180deg, #143b29, #0d2c1e) !important;
    color: var(--cis-text) !important;
    box-shadow: 0 0 12px rgba(72,245,163,.10) !important;
}
.stButton button:hover,
.stFormSubmitButton button:hover {
    border-color: var(--cis-accent) !important;
    color: var(--cis-accent-soft) !important;
}

/* Expanders and forms */
details[data-testid="stExpander"],
[data-testid="stForm"] {
    background: rgba(13,33,24,.78) !important;
    border: 1px solid var(--cis-border) !important;
    border-radius: 16px !important;
}
details[data-testid="stExpander"] summary,
details[data-testid="stExpander"] summary * {
    color: var(--cis-text) !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: var(--cis-muted) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--cis-accent-soft) !important;
    border-bottom-color: var(--cis-accent) !important;
}
button[data-baseweb="tab"]:hover {
    color: var(--cis-text) !important;
}

/* Metrics */
div[data-testid="metric-container"] {
    background: rgba(13,33,24,.78) !important;
    border: 1px solid var(--cis-border) !important;
    border-radius: 15px !important;
    padding: .75rem .85rem !important;
}
[data-testid="stMetricValue"] {
    color: var(--cis-accent-soft) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--cis-muted) !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid var(--cis-border) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    background: #f8faf9 !important;
}
[data-testid="stDataFrame"] * {
    color: #13231b !important;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 14px !important;
    border: 1px solid var(--cis-border) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {
    color: var(--cis-text) !important;
}

/* Dividers */
hr {
    border-color: rgba(92,255,174,.16) !important;
}

/* Mobile/tablet */
@media (max-width: 768px) {
    .block-container {
        padding-left: .9rem !important;
        padding-right: .9rem !important;
        padding-top: 1.2rem !important;
    }
    h1 {
        font-size: 2.15rem !important;
        line-height: 1.15 !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: .65rem !important;
    }
}
</style>
"""

if st is not None and not getattr(st, "_cis_theme_wrapped", False):
    _original_set_page_config = st.set_page_config

    def _cis_set_page_config(*args, **kwargs):
        result = _original_set_page_config(*args, **kwargs)
        st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
        return result

    st.set_page_config = _cis_set_page_config
    st._cis_theme_wrapped = True
