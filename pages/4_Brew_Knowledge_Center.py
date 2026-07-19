from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


st.set_page_config(
    page_title="Brew Knowledge Center",
    page_icon="📚",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "brew_knowledge.json"


def load_articles() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def resolve_asset(relative_path: str) -> Path:
    return BASE_DIR / relative_path


def article_matches(article: dict[str, Any], query: str) -> bool:
    if not query:
        return True

    haystack = " ".join(
        [
            str(article.get("title", "")),
            str(article.get("category", "")),
            str(article.get("subcategory", "")),
            str(article.get("summary", "")),
            str(article.get("pagerwatu_note", "")),
            " ".join(article.get("tags", [])),
        ]
    ).lower()

    return query.lower().strip() in haystack


st.markdown(
    """
    <style>
    .kc-card {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 1rem;
        background: rgba(250,250,250,.55);
    }
    .kc-meta {
        color: #6b7280;
        font-size: .92rem;
        margin-bottom: .45rem;
    }
    .kc-summary {
        line-height: 1.55;
    }
    .kc-tag {
        display: inline-block;
        border: 1px solid rgba(128,128,128,.28);
        border-radius: 999px;
        padding: .18rem .55rem;
        margin: .15rem .15rem .15rem 0;
        font-size: .82rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📚 Brew Knowledge Center")
st.caption("Perpustakaan visual untuk ilmu brewing, extraction, grinder, water, dan troubleshooting.")

articles = load_articles()

if not articles:
    st.warning("Belum ada materi knowledge di database.")
    st.stop()

categories = sorted({str(item.get("category", "Uncategorized")) for item in articles})

filter_col, search_col = st.columns([1, 2])
with filter_col:
    category_filter = st.selectbox("Kategori", ["Semua"] + categories, index=0)

with search_col:
    search_query = st.text_input(
        "Cari knowledge",
        placeholder="Contoh: espresso terlalu asam, grind size, suhu air...",
    )

filtered = [
    item
    for item in articles
    if (category_filter == "Semua" or item.get("category") == category_filter)
    and article_matches(item, search_query)
]

st.caption(f"{len(filtered)} materi ditemukan")
st.divider()

if not filtered:
    st.info("Tidak ada materi yang cocok dengan filter atau pencarian.")
    st.stop()

for article in filtered:
    title = article.get("title", "Untitled")
    category = article.get("category", "Uncategorized")
    subcategory = article.get("subcategory", "")
    source = article.get("source", "-")
    status = article.get("status", "Reference")
    summary = article.get("summary", "")
    note = article.get("pagerwatu_note", "")
    tags = article.get("tags", [])
    image_paths = article.get("images", [])

    st.markdown(
        f"""
        <div class="kc-card">
            <h3>{title}</h3>
            <div class="kc-meta">{category} · {subcategory} · {status}</div>
            <div class="kc-summary">{summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    detail_tab, gallery_tab, note_tab = st.tabs(
        ["📌 Ringkasan", "🖼️ Galeri", "📝 Catatan Pagerwatu"]
    )

    with detail_tab:
        st.markdown(f"**Sumber:** {source}")
        if tags:
            st.markdown(
                "".join(f'<span class="kc-tag">{tag}</span>' for tag in tags),
                unsafe_allow_html=True,
            )

    with gallery_tab:
        valid_images = [resolve_asset(path) for path in image_paths]
        valid_images = [path for path in valid_images if path.exists()]

        if not valid_images:
            st.warning("File gambar untuk materi ini tidak ditemukan.")
        else:
            for start in range(0, len(valid_images), 2):
                cols = st.columns(2)
                for col, image_path in zip(cols, valid_images[start:start + 2]):
                    with col:
                        st.image(
                            str(image_path),
                            use_container_width=True,
                            caption=f"Halaman {valid_images.index(image_path) + 1}",
                        )

    with note_tab:
        if note:
            st.info(note)
        else:
            st.caption("Belum ada catatan internal Pagerwatu.")

    st.divider()

st.caption("© 2026 Pagerwatu Brew & Roastery")
