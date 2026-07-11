import streamlit as st

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Coffee Intelligent System",
    page_icon="☕",
    layout="wide"
)

# ==========================================
# HEADER
# ==========================================
st.title("☕ Coffee Intelligent System")
st.caption("Green Bean Database • Version V10.1")

st.divider()

# ==========================================
# WELCOME
# ==========================================
st.subheader("Welcome")

st.write(
    """
Selamat datang di **Coffee Intelligent System (CIS)**.

Project ini dibangun untuk menjadi pusat seluruh aktivitas kopi Pagerwatu.

Silakan mulai dari **Green Bean Database**.
"""
)

st.divider()

# ==========================================
# MODULE STATUS
# ==========================================
st.subheader("Current Modules")

col1, col2 = st.columns(2)

with col1:
    st.success("🌱 Green Bean Database")

with col2:
    st.info("🔥 Roast Profile (Coming Soon)")

st.divider()

# ==========================================
# FOOTER
# ==========================================
st.caption("© 2026 Pagerwatu Coffee")
