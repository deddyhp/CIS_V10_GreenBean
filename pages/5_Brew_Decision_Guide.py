from __future__ import annotations
import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Brew Decision Guide", page_icon="🧭", layout="wide")
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "brew_decision_guide.json"

def load_records():
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def matches(record, query):
    if not query.strip():
        return True
    text = " ".join([
        str(record.get("title","")), str(record.get("dripper","")), str(record.get("paper","")),
        str(record.get("goal","")), " ".join(record.get("bean_fit",[])),
        " ".join(record.get("reason",[])), " ".join(record.get("troubleshooting",{}).keys()),
        " ".join(record.get("troubleshooting",{}).values())
    ]).lower()
    return query.lower().strip() in text

st.markdown("""
<style>
:root { --bg:#07120d; --line:rgba(78,255,171,.20); --text:#eafef2; --muted:#a8c7b4; --accent2:#8affca; }
.stApp { background: radial-gradient(circle at top right, rgba(54,245,155,0.12), transparent 28%), linear-gradient(180deg, var(--bg), #06110c 100%); color: var(--text); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #08150f, #07120d); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] * { color: var(--text) !important; }
.header-panel, .guide-card { border:1px solid var(--line); border-radius:20px; padding:1.1rem 1.2rem; background:rgba(12,28,22,.9); box-shadow:0 0 14px rgba(78,255,171,.10); margin-bottom:1rem; }
.small-meta { color:#a8c7b4; font-size:.92rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-panel"><h1>🧭 Brew Decision Guide</h1><p class="small-meta">Dripper → Paper → Goal rasa → Bean cocok → Resep utama → Troubleshooting</p></div>', unsafe_allow_html=True)

records = load_records()
if not records:
    st.warning("Database Brew Decision Guide belum tersedia.")
    st.stop()

drippers = ["Semua"] + sorted({r.get("dripper","-") for r in records})
papers = ["Semua"] + sorted({r.get("paper","-") for r in records})
goals = ["Semua"] + sorted({r.get("goal","-") for r in records})

c1,c2,c3 = st.columns(3)
with c1: selected_dripper = st.selectbox("Dripper", drippers)
with c2: selected_paper = st.selectbox("Paper", papers)
with c3: selected_goal = st.selectbox("Goal rasa", goals)

query = st.text_input("Cari berdasarkan bean, rasa, atau masalah", placeholder="Contoh: Kenya, floral, terlalu asam...")

filtered = [r for r in records if (selected_dripper == "Semua" or r.get("dripper") == selected_dripper) and (selected_paper == "Semua" or r.get("paper") == selected_paper) and (selected_goal == "Semua" or r.get("goal") == selected_goal) and matches(r, query)]
st.caption(f"{len(filtered)} resep ditemukan")
st.divider()

for record in filtered:
    st.markdown(f'<div class="guide-card"><h3>{record.get("title","Untitled")}</h3><div class="small-meta">{record.get("dripper")} · {record.get("paper")} · {record.get("status")}</div><p><strong>Goal:</strong> {record.get("goal","-")}</p></div>', unsafe_allow_html=True)
    tabs = st.tabs(["☕ Resep", "🧠 Alasan", "🎯 Target Rasa", "🛠 Troubleshooting", "📝 Catatan"])
    with tabs[0]:
        a,b,c,d = st.columns(4)
        a.metric("Dose", f'{record.get("dose_g","-")} g')
        b.metric("Water", f'{record.get("water_g","-")} g')
        c.metric("Ratio", record.get("ratio","-"))
        d.metric("Brew Time", record.get("brew_time","-"))
        st.markdown(f'**Temperature:** {record.get("temperature_c","-")}')
        st.markdown(f'**Grind:** {record.get("grind","-")}')
        st.markdown(f'**DF64 start:** {record.get("df64_start","-")}')
        st.markdown("**Pouring:**")
        for step in record.get("pouring", []): st.write(f"• {step}")
        st.markdown("**Bean yang cocok:**")
        for bean in record.get("bean_fit", []): st.write(f"• {bean}")
    with tabs[1]:
        for item in record.get("reason", []): st.write(f"• {item}")
    with tabs[2]:
        for key, value in record.get("target_profile", {}).items(): st.markdown(f"**{key.title()}:** {value}")
    with tabs[3]:
        for issue, solution in record.get("troubleshooting", {}).items():
            st.markdown(f"**{issue}**")
            st.write(solution)
    with tabs[4]:
        st.info(record.get("notes", "Belum ada catatan."))
    st.divider()

st.caption("© 2026 Pagerwatu Brew & Roastery")
