from __future__ import annotations
import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Brew Knowledge Center", page_icon="📚", layout="wide")
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "brew_knowledge.json"

def load_articles():
    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except Exception:
        return []

def resolve_asset(relative_path: str) -> Path:
    return BASE_DIR / relative_path

def article_matches(article, query):
    if not query.strip():
        return True
    haystack = " ".join([
        str(article.get("title", "")), str(article.get("category", "")),
        str(article.get("subcategory", "")), str(article.get("summary", "")),
        str(article.get("pagerwatu_note", "")), " ".join(article.get("tags", [])),
    ]).lower()
    return query.lower().strip() in haystack

st.markdown("""
<style>
:root { --bg:#07120d; --line:rgba(78,255,171,.20); --text:#eafef2; --muted:#a8c7b4; --accent2:#8affca; }
.stApp { background: radial-gradient(circle at top right, rgba(54,245,155,0.12), transparent 28%), linear-gradient(180deg, var(--bg), #06110c 100%); color: var(--text); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #08150f, #07120d); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] * { color: var(--text) !important; }
.kc-card, .header-panel { border:1px solid var(--line); border-radius:20px; padding:1.1rem 1.2rem; background:rgba(12,28,22,.9); box-shadow:0 0 14px rgba(78,255,171,.10); margin-bottom:1rem; }
.kc-meta { color: var(--muted); font-size:.92rem; margin-bottom:.45rem; }
.kc-tag { display:inline-block; border:1px solid var(--line); border-radius:999px; padding:.18rem .55rem; margin:.15rem .15rem .15rem 0; font-size:.82rem; color:var(--accent2); background:rgba(54,245,155,.07); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-panel"><h1>📚 Brew Knowledge Center</h1><p class="kc-meta">Perpustakaan visual untuk brewing, extraction, grinder, water, dan troubleshooting.</p></div>', unsafe_allow_html=True)

articles = load_articles()
if not articles:
    st.warning("Belum ada materi knowledge di database.")
    st.stop()

categories = sorted({str(item.get("category", "Uncategorized")) for item in articles})
c1, c2 = st.columns([1,2])
with c1:
    category_filter = st.selectbox("Kategori", ["Semua"] + categories)
with c2:
    search_query = st.text_input("Cari knowledge", placeholder="Contoh: espresso, grind size, suhu air...")

filtered = [item for item in articles if (category_filter == "Semua" or item.get("category") == category_filter) and article_matches(item, search_query)]
st.caption(f"{len(filtered)} materi ditemukan")
st.divider()

for article in filtered:
    st.markdown(f'<div class="kc-card"><h3>{article.get("title","Untitled")}</h3><div class="kc-meta">{article.get("category","Uncategorized")} · {article.get("subcategory","")} · {article.get("status","Reference")}</div><div>{article.get("summary","")}</div></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📌 Ringkasan", "🖼️ Galeri", "📝 Catatan Pagerwatu"])
    with t1:
        st.markdown(f"**Sumber:** {article.get('source','-')}")
        tags = article.get("tags", [])
        if tags:
            st.markdown("".join(f'<span class="kc-tag">{tag}</span>' for tag in tags), unsafe_allow_html=True)
    with t2:
        valid_images = [resolve_asset(path) for path in article.get("images", [])]
        valid_images = [path for path in valid_images if path.exists()]
        if valid_images:
            for start in range(0, len(valid_images), 2):
                cols = st.columns(2)
                for col, image_path in zip(cols, valid_images[start:start+2]):
                    with col:
                        st.image(str(image_path), use_container_width=True, caption=f"Halaman {valid_images.index(image_path)+1}")
        else:
            st.warning("File gambar untuk materi ini tidak ditemukan.")
    with t3:
        note = article.get("pagerwatu_note", "")
        st.info(note if note else "Belum ada catatan internal Pagerwatu.")
    st.divider()

st.caption("© 2026 Pagerwatu Brew & Roastery")
