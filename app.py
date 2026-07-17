import streamlit as st

st.set_page_config(
    page_title="Coffee Intelligent System",
    page_icon="☕",
    layout="wide"
)

# =========================
# CSS
# =========================
st.markdown("""
<style>

/* Sidebar */
section[data-testid="stSidebar"] *{
    font-size:20px !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{
    font-size:26px !important;
    font-weight:bold;
}

/* Dashboard Cards */
.card{
    border:1px solid #dddddd;
    border-radius:14px;
    padding:24px;
    background:#fafafa;
    margin-bottom:18px;
}

.card h2{
    margin-bottom:8px;
}

.footer{
    text-align:center;
    color:#888;
    margin-top:40px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================

st.title("☕ Coffee Intelligent System")
st.caption("New CIS • Version 11.0")

st.divider()

st.subheader("Welcome 👋")

st.write(
    """
Coffee Intelligent System (CIS) adalah pusat database dan tools
untuk mendukung aktivitas **Pagerwatu Brew & Roastery**.

Silakan pilih workspace melalui sidebar.
"""
)

st.divider()

# =========================
# MAIN MODULES
# =========================

col1, col2 = st.columns(2)

with col1:

    st.markdown("""
<div class="card">

## 🌱 Green Bean

Inventory Management

- Coffee Database
- Stock
- Transactions
- Bean Information

</div>
""", unsafe_allow_html=True)

with col2:

    st.markdown("""
<div class="card">

## ☕ Brew Things

Coffee Brewing Workspace

- Brewing Recipes
- Brewing Guide
- Extraction
- Water

</div>
""", unsafe_allow_html=True)

st.divider()

# =========================
# STATUS
# =========================

st.subheader("System Status")

st.success("✅ Green Bean Database Ready")

st.info("☕ Brew Things Development")

st.divider()

# =========================
# FOOTER
# =========================

st.markdown(
    """
<div class="footer">

© 2026 Pagerwatu Brew & Roastery

</div>
""",
unsafe_allow_html=True)
