import streamlit as st

import utils.brew_database as brew_db


st.set_page_config(
    page_title="Brew & Things",
    page_icon="☕",
    layout="wide",
)

st.markdown(
    """
    <style>
    div[data-testid="stSidebarNav"] a,
    div[data-testid="stSidebarNav"] span,
    div[data-testid="stSidebarNav"] p {
        font-size: 22px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("☕ Brew & Things")
st.caption("Coffee Intelligence System • V20.0 • Step 1 Database Connection")

st.info(
    "Tahap ini hanya memastikan koneksi Google Sheets dan struktur lima worksheet. "
    "Recipe Library akan dibangun pada Step 2."
)

refresh = st.button("🔄 Refresh Connection")

if refresh:
    brew_db.clear_connection_cache()
    st.rerun()

try:
    with st.spinner("Connecting to CIS Brew Things Google Sheet..."):
        brew_db.ensure_database_structure()
        status_df = brew_db.get_database_status()
except Exception as exc:
    st.error(f"Koneksi Brew Things belum berhasil: {exc}")
    st.stop()

st.success("✅ Brew Things Google Sheet connected.")

ready_count = int((status_df["Status"] == "Ready").sum())
total_rows = int(status_df["Data Rows"].sum())

metric1, metric2, metric3 = st.columns(3)
metric1.metric("Worksheets Ready", f"{ready_count}/5")
metric2.metric("Total Data Rows", total_rows)
metric3.metric("Database", "Google Sheets")

st.subheader("Database Status")
st.dataframe(
    status_df,
    use_container_width=True,
    hide_index=True,
)

if ready_count == 5:
    st.success("✅ Semua worksheet dan header siap untuk Step 2 — Recipe Library.")
else:
    st.warning(
        "Ada header yang belum lengkap. Script akan menambahkan header yang hilang "
        "tanpa menghapus data lama."
    )

with st.expander("🔎 Test Settings Dropdown"):
    categories = [
        "Brew_Method",
        "Ownership",
        "Purpose",
        "Status",
        "Favorite",
    ]

    for category in categories:
        values = brew_db.get_settings(category)
        st.markdown(
            f"**{category}:** {', '.join(values) if values else 'Belum ada data'}"
        )
