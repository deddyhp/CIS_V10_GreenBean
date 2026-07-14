import streamlit as st

st.markdown("""
<style>

/* Sidebar */

section[data-testid="stSidebar"] *{
    font-size: 22px !important;
}

/* Judul halaman sidebar */

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{
    font-size: 28px !important;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="Coffee Intelligent System",
    page_icon="☕",
    layout="wide"
)

st.title("☕ Coffee Intelligent System")
st.caption("Version V10.8")

st.divider()

st.markdown("""
Selamat datang di **Coffee Intelligent System (CIS)**.

Silakan pilih modul melalui **sidebar** di sebelah kiri.

### Current Modules
- 🌱 Green Bean Database
- 🔥 Roast Profile *(Coming Soon)*
- ☕ Blend Database *(Coming Soon)*
- 📦 Inventory *(Coming Soon)*
- 📈 Analytics *(Coming Soon)*
""")

st.info("👈 Gunakan menu di kiri untuk membuka modul.")

st.divider()

st.caption("© 2026 Pagerwatu Brew & Roastery")
