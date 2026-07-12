import streamlit as st

st.set_page_config(
    page_title="Coffee Intelligent System",
    page_icon="☕",
    layout="wide"
)

st.title("☕ Coffee Intelligent System")
st.caption("Version V10.1")

st.divider()

st.subheader("🏠 Home")

st.write("""
Selamat datang di **Coffee Intelligent System (CIS)**.

Gunakan menu di sidebar untuk membuka setiap modul.

Saat ini modul yang aktif adalah:

- 🌱 Green Bean Database
""")

st.divider()

st.success("✅ System Ready")

st.caption("© 2026 Pagerwatu Coffee")
