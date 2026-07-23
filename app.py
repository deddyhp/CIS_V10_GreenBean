import streamlit as st

st.set_page_config(page_title="Coffee Intelligent System", page_icon="☕", layout="wide")

st.markdown("""
<style>
:root { --bg:#07120d; --panel:rgba(14,31,24,.88); --line:rgba(78,255,171,.20); --text:#eafef2; --muted:#a8c7b4; --accent2:#8affca; }
.stApp { background: radial-gradient(circle at top right, rgba(54,245,155,0.12), transparent 28%), radial-gradient(circle at left bottom, rgba(54,245,155,0.08), transparent 25%), linear-gradient(180deg, var(--bg), #06110c 100%); color: var(--text); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #08150f, #07120d); border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] * { color: var(--text) !important; font-size: 18px !important; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.hero { padding:1.6rem; border:1px solid var(--line); border-radius:22px; background: linear-gradient(180deg, rgba(16,38,29,0.95), rgba(9,20,16,0.96)); box-shadow:0 0 14px rgba(78,255,171,.18); margin-bottom:1.3rem; }
.hero-badge { display:inline-block; padding:.35rem .8rem; border:1px solid var(--line); border-radius:999px; color:var(--accent2); font-size:.84rem; margin-bottom:.8rem; background:rgba(54,245,155,.07); }
.info-card { border:1px solid var(--line); border-radius:18px; padding:1.1rem; background: linear-gradient(180deg, rgba(12,28,22,.92), rgba(9,19,15,.88)); box-shadow:0 0 14px rgba(78,255,171,.10); min-height:240px; }
.info-card h3 { color: var(--accent2); }
.stat-box { border:1px solid var(--line); border-radius:16px; padding:.95rem 1rem; background: rgba(8,19,15,.82); text-align:center; box-shadow:0 0 14px rgba(78,255,171,.10); }
.stat-box .num { font-size:1.5rem; font-weight:700; color:var(--accent2); }
.stat-box .label { color:var(--muted); font-size:.88rem; }
.section-title { color: var(--accent2); margin-top: .2rem; margin-bottom: .8rem; }
.footer { color:#89a696; text-align:center; margin-top:1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-badge">☕ NEW CIS · Green Bean + Brew Things</div>
    <h1 style="margin:0;font-size:3rem;line-height:1.05;">Coffee Intelligent System</h1>
    <p style="color:#a8c7b4;font-size:1rem;margin-top:.7rem;">
        Dashboard utama Pagerwatu untuk Green Bean Database dan Brew Things.
        Fokus pada utilization harian, visual knowledge, dan decision guide brewing.
    </p>
</div>
""", unsafe_allow_html=True)

s1,s2,s3,s4 = st.columns(4)
with s1: st.markdown('<div class="stat-box"><div class="num">2</div><div class="label">Core Pillars</div></div>', unsafe_allow_html=True)
with s2: st.markdown('<div class="stat-box"><div class="num">9</div><div class="label">Brew Guide Setups</div></div>', unsafe_allow_html=True)
with s3: st.markdown('<div class="stat-box"><div class="num">1</div><div class="label">Knowledge Center</div></div>', unsafe_allow_html=True)
with s4: st.markdown('<div class="stat-box"><div class="num">Cloud</div><div class="label">Tablet / HP Ready</div></div>', unsafe_allow_html=True)

st.markdown('<h3 class="section-title">Workspace</h3>', unsafe_allow_html=True)
c1,c2 = st.columns(2)
with c1:
    st.markdown("""
    <div class="info-card">
        <h3>🌱 Green Bean Database</h3>
        <p style="color:#a8c7b4;">Inventory dan database green bean untuk kebutuhan operasional CIS.</p>
        <ul style="color:#a8c7b4;">
            <li>Stock & transaksi</li>
            <li>Bean information</li>
            <li>Utilization harian</li>
            <li>Ready untuk pemakaian real</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="info-card">
        <h3>☕ Brew Things</h3>
        <p style="color:#a8c7b4;">Ruang brewing yang berisi knowledge dan decision guide.</p>
        <ul style="color:#a8c7b4;">
            <li>Brew Knowledge Center</li>
            <li>Brew Decision Guide</li>
            <li>9 kombinasi dripper-paper</li>
            <li>AI Recommended → Trial → Locked</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.markdown('<h3 class="section-title">Current Direction</h3>', unsafe_allow_html=True)
st.info("CIS difokuskan untuk Green Bean dan Brew Things. Roast Profile berada di proyek terpisah: RPA.")
st.markdown('<div class="footer">© 2026 Pagerwatu Brew & Roastery</div>', unsafe_allow_html=True)
