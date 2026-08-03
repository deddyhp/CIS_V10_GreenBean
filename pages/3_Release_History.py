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

st.subheader("☕ New CIS System")
for ver, status, note in [
    ("V10.16", "Chaty Save Fix", "Memperbaiki penyimpanan hasil Update Chaty ke Plan Library dengan session-state-safe rerun, serta memperjelas kontras tulisan pada tombol utama di tablet."),
    ("V10.15", "Flexible Chaty Parser", "Update Chaty sekarang menerima format metadata satu baris maupun dua baris, misalnya BEAN: Arabika Gayo atau label BEAN diikuti nilainya pada baris berikutnya."),
    ("V10.14", "Chaty Plan Import", "Menambahkan menu Update Chaty: copy–paste blok CIS ROASTING PLAN, parse & preview editable, lalu simpan ke Plan Library yang sama. Library kini menampilkan badge dan filter sumber Chaty Import atau Manual Plan."),
    ("V10.13", "Complete S³ Roasting Guide", "Baseline editable sekarang terisi lengkap dari Preheat, Drying, Maillard, First Crack, Development sampai Drop. Plan Library menampilkan Juklak Praktis S³ otomatis sebagai ringkasan operasional sebelum detail per fase."),
    ("V10.12", "Editable Roasting Baseline", "Create Plan sekarang langsung terisi baseline editable: batch 500 g, preheat BT 200°C · A40 · drum 90 rpm, stabilisasi 2–3 menit, serta checkpoint drying Charge G45/A40, TP G55/A40, BT110 G65/A40, BT130 G65/A50, dan target Dry End 147–149°C @ 4:05–4:20."),
    ("V10.11", "Roasting Plan Utility", "Roasting Plan ditambahkan sebagai utility tablet/HP tanpa mengubah dua core pillar CIS. Data plan disimpan pada worksheet Google Sheets roasting_plans; RPA tetap menangani roast log dan analisis aktual."),
]:
    st.markdown(f'<div class="record"><h4>{ver}</h4><div class="muted"><strong>{status}</strong></div><p><strong>What\'s New:</strong> {note}</p></div>', unsafe_allow_html=True)

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


st.subheader("🔥 Roasting Plan Utility")
for ver, status, note in [
    ("V1.5", "Library Save & Button Visibility Fix", "Memperbaiki error session_state saat menyimpan Chaty Plan, membersihkan kotak copy-paste secara aman setelah sukses, dan meningkatkan keterbacaan label tombol utama pada tablet."),
    ("V1.4", "Flexible Metadata Parsing", "Parser Chaty menerima PLAN NAME, BEAN, PURPOSE, GOAL, BATCH, DENSITY, MOISTURE, dan STATUS baik dalam format label: nilai maupun label pada satu baris lalu nilai pada baris berikutnya."),
    ("V1.3", "Chaty Import Workflow", "Dua jalur input tersedia: Create Manual untuk trial mandiri dan Update Chaty untuk copy–paste juklak terstruktur. Keduanya bermuara ke Plan Library, S³ Guide, rating, evaluation, duplicate, dan recall."),
    ("V1.2", "Complete Practical Guide", "Seluruh fase memiliki baseline editable dan Guide Mode kini otomatis menyusun ringkasan Juklak Praktis S³: Preheat/Charge, Drying Gates, Maillard Gates, FC–Development, Drop/Cooling, serta S³ Control."),
    ("V1.1", "Editable Baseline Template", "Plan baru dilengkapi angka baseline awal yang seluruhnya bisa diedit, sehingga form tidak lagi kosong dan lebih cepat dipakai sebagai juklak roasting."),
    ("V1.0", "New Utility", "Menambahkan manual Roasting Plan, S³ Guide Mode, Plan Library, search & recall, rating 0–5 dengan interval 0.5, usage count, evaluation, duplicate version, serta penyimpanan Google Sheets untuk penggunaan tablet/HP saat roasting."),
]:
    st.markdown(f'<div class="record"><h4>{ver}</h4><div class="muted"><strong>{status}</strong></div><p><strong>What\'s New:</strong> {note}</p></div>', unsafe_allow_html=True)

st.subheader("Project Direction")
st.success("Build → Real Data Input → Utilization → HVPT → Running Smooth → Advanced")
st.caption("Roasting Plan adalah utility operasional di CIS. Roast log, kurva aktual, dan evaluasi profile tetap dikembangkan terpisah di RPA.")
