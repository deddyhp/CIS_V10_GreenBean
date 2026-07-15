import streamlit as st


st.set_page_config(
    page_title="CIS Release History",
    page_icon="📖",
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

    .main .block-container {
        max-width: 1050px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        letter-spacing: -0.02em;
    }

    hr {
        margin-top: 1.2rem;
        margin-bottom: 1.5rem;
    }

    .release-card {
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 14px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.8rem;
    }

    .release-version {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .release-status {
        font-size: 0.9rem;
        opacity: 0.72;
        margin-bottom: 0.5rem;
    }

    .release-note {
        font-size: 1rem;
        line-height: 1.55;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def release_card(version: str, status: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="release-card">
            <div class="release-version">{version}</div>
            <div class="release-status">{status}</div>
            <div class="release-note"><b>What's New:</b> {note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.title("📖 CIS Release History")
st.caption("Coffee Intelligence System • Version Achievement Record")
st.divider()

st.markdown(
    """
Halaman ini mencatat **achievement version penting** dari tiga database utama CIS.

Setiap versi hanya menampilkan perubahan utama agar riwayat perkembangan tetap cepat dibaca.
"""
)

st.divider()

st.header("🌱 Green Bean")

release_card(
    "V10.8",
    "Stable Utilization",
    "Database dipindahkan ke Google Sheets agar lebih mudah digunakan lintas device. "
    "Add, revise, properties, stock adjustment, dan update history sudah berjalan untuk utilisasi nyata.",
)

release_card(
    "V10.7",
    "Stable Utilization",
    "Tampilan menu sidebar diperbesar tanpa mengubah navigation maupun database logic.",
)

release_card(
    "V10.6",
    "Stable",
    "Simple Inventory View selesai. Bean properties dapat dibuka dari stock list dan remaining stock dapat diperbarui.",
)

st.divider()

st.header("🔥 Roast Profile")

release_card(
    "V04.4",
    "Stable Database",
    "Import roast profile, penyimpanan roast log, pembukaan kembali data roast, serta tampilan trend dan database "
    "sudah berjalan sebagai fondasi utilisasi.",
)

release_card(
    "V04.3",
    "Development Achievement",
    "Database roast mulai diaktifkan sebagai database hidup, bukan hanya tempat import single roast.",
)

release_card(
    "V04.2",
    "Development Achievement",
    "Struktur import roast dan penyajian data profile mulai distabilkan untuk penggunaan berulang.",
)

st.divider()

st.header("☕ Brew Things")

release_card(
    "V20.4.1",
    "Stable Improvement",
    "Minor refinement setelah V20.4 dengan tetap mempertahankan struktur database dan flow penggunaan utama.",
)

release_card(
    "V20.4",
    "Stable Achievement",
    "Core Brew Things selesai dengan Brew Recipe, Favorite Recipe, serta Lab & Trial Recipe sebagai tiga fungsi utama.",
)

release_card(
    "V20.3",
    "Development Achievement",
    "Struktur recipe mulai dipisahkan berdasarkan fungsi penggunaan agar recipe harian dan trial tidak bercampur.",
)

st.divider()

st.subheader("Project Direction")
st.markdown(
    """
> **Build → Real Data Input → Utilization → HVPT → Running Smooth → Advanced**

Versi baru hanya dibuat ketika membawa achievement yang jelas, bukan sekadar perubahan kecil tanpa nilai penggunaan.
"""
)

st.caption("CIS Homepage • Global Version Reference")
