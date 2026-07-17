import streamlit as st

st.set_page_config(
    page_title="CIS Release History",
    page_icon="📖",
    layout="wide"
)

st.title("📖 CIS Release History")
st.caption("Coffee Intelligent System - Version Achievement Record")

st.divider()

st.write("""
Halaman ini mencatat achievement version penting dari modul utama New CIS.

Setiap versi hanya menampilkan perubahan utama agar riwayat perkembangan tetap ringkas dan mudah dibaca.
""")

st.divider()

# ==========================================================
# GREEN BEAN
# ==========================================================

st.header("🌱 Green Bean")

st.info("""
**V10.8**  
**Stable Utilization**

**What's New:** Database dipindahkan ke Google Sheets agar mudah digunakan lintas perangkat.
""")

st.info("""
**V10.7**  
**Stable Utilization**

**What's New:** Sidebar diperbesar tanpa mengubah navigation maupun database logic.
""")

st.info("""
**V10.6**  
**Stable**

**What's New:** Inventory mulai digunakan sebagai database operasional harian.
""")

st.divider()

# ==========================================================
# BREW THINGS
# ==========================================================

st.header("☕ Brew Things")

st.info("""
**V20.4.1**  
**Stable Improvement**

**What's New:** Penyempurnaan Brew Recipe dan struktur database.
""")

st.info("""
**V20.4**  
**Stable Achievement**

**What's New:** Core Brew Things selesai dengan Brew Recipe, Favorite Recipe, serta Lab & Trial Recipe.
""")

st.info("""
**V20.3**  
**Development Achievement**

**What's New:** Struktur recipe dipisahkan berdasarkan fungsi penggunaan.
""")

st.divider()

# ==========================================================
# PROJECT DIRECTION
# ==========================================================

st.header("Project Direction")

st.success("""
Build
➡ Real Data Input
➡ Utilization
➡ HVPT
➡ Running Smooth
➡ Advanced
""")

st.caption("""
Mulai New CIS, Roast Profile dikembangkan sebagai proyek terpisah (RPA).
Release History CIS hanya mencatat perkembangan Green Bean dan Brew Things.
""")
