import streamlit as st

GLOBAL_CSS = r"""
<style>
.stApp {
    background:
        radial-gradient(circle at 85% 0%, rgba(72,245,163,.13), transparent 28%),
        radial-gradient(circle at 0% 100%, rgba(72,245,163,.08), transparent 25%),
        linear-gradient(180deg, #06110c, #04100a 100%) !important;
    color: #f2fff7 !important;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07160f, #06110c) !important;
    border-right: 1px solid rgba(92,255,174,.30) !important;
}
section[data-testid="stSidebar"] * { color:#f2fff7 !important; }
h1,h2,h3,h4,h5,h6,[data-testid="stMetricValue"] { color:#f2fff7 !important; }
p,li,label,[data-testid="stCaptionContainer"],[data-testid="stMetricLabel"],[data-testid="stWidgetLabel"] {
    color:#c7ddcf !important;
}
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div,
.stTextInput input,.stNumberInput input,.stTextArea textarea {
    background:#f5f8f6 !important;
    color:#102019 !important;
    border-radius:11px !important;
}
button[data-baseweb="tab"] { color:#c7ddcf !important; }
button[data-baseweb="tab"][aria-selected="true"] { color:#95ffd0 !important; }
div[data-testid="metric-container"] {
    background:rgba(13,33,24,.78) !important;
    border:1px solid rgba(92,255,174,.30) !important;
    border-radius:15px !important;
    padding:.75rem .85rem !important;
}
[data-testid="stMetricValue"] { color:#95ffd0 !important; }
[data-testid="stDataFrame"] {
    border:1px solid rgba(92,255,174,.30) !important;
    border-radius:14px !important;
    overflow:hidden !important;
    background:#f8faf9 !important;
}
[data-testid="stDataFrame"] * { color:#13231b !important; }
[data-testid="stAlert"] p,[data-testid="stAlert"] div,[data-testid="stAlert"] span {
    color:#f2fff7 !important;
}
@media (max-width:768px) {
    .block-container { padding-left:.9rem !important; padding-right:.9rem !important; }
    h1 { font-size:2.15rem !important; }
}
</style>
"""

def apply_cis_theme():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
