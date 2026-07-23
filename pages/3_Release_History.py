import streamlit as st

st.set_page_config(page_title="CIS Release History", page_icon="📖", layout="wide")
st.markdown("""
<style>
:root { --bg:#07120d; --line:rgba(78,255,171,.20); --text:#eafef2; --muted:#a8c7b4; --accent2:#8affca; }
.stApp { background: radial-gradient(circle at top right, rgba(54,245,155,0.12), transparent 28%), linear-gradient(180deg, var(--bg), #06110c 100%); color: var(--text); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #08150f, #07120d); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] * { color: var(--text) !important; }
.record, .header-panel { border:1px solid var(--line); border-radius:20px; padding:1.1rem 1.2rem; background:rgba(12,28,22,.9); box-shadow:0 0 14px rgba(78,255,171,.10); margin-bottom:1rem; }
.record h4 { color: var(--accent2); margin:.1rem 0 .3rem 0; }
.muted { color: var(--muted); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-panel">
<h1>📖 CIS Release History</h1>
<p class="muted">Coffee Intelligent System · Version Achievement Record</p>
<p class="muted">Riwayat achievement utama New CIS dengan fokus Green Bean dan Brew Things.</p>
</div>
""", unsafe_allow_html=True)

st.subheader("🌱 Green Bean")
for ver, status, note in [
    ("V10.8", "Stable Utilization", "Database dipindahkan ke Google Sheets agar lebih mudah digunakan lintas perangkat."),
    ("V10.7", "Stable Utilization", "Tampilan sidebar diperbesar tanpa mengubah navigation maupun logic utama."),
    ("V10.6", "Stable", "Inventory mulai digunakan sebagai database operasional harian.")
]:
    st.markdown(f'<div class="record"><h4>{ver}</h4><div class="muted"><strong>{status}</strong></div><p><strong>What\'s New:</strong> {note}</p></div>', unsafe_allow_html=True)

st.subheader("☕ Brew Things")
for ver, status, note in [
    ("V21.0", "UI Refresh + Expansion", "Theme futuristik hijau diterapkan, Brew Knowledge Center dipoles, dan Brew Decision Guide dilengkapi 9 kombinasi dripper-paper."),
    ("V20.4.1", "Stable Improvement", "Penyempurnaan struktur Brew Recipe dan flow penggunaan utama."),
    ("V20.4", "Stable Achievement", "Core Brew Things selesai dengan Brew Recipe, Favorite Recipe, serta Lab & Trial Recipe."),
    ("V20.3", "Development Achievement", "Struktur recipe mulai dipisahkan berdasarkan fungsi penggunaan.")
]:
    st.markdown(f'<div class="record"><h4>{ver}</h4><div class="muted"><strong>{status}</strong></div><p><strong>What\'s New:</strong> {note}</p></div>', unsafe_allow_html=True)

st.subheader("Project Direction")
st.success("Build → Real Data Input → Utilization → HVPT → Running Smooth → Advanced")
st.caption("Mulai New CIS, Roast Profile dikembangkan sebagai proyek terpisah (RPA).")
