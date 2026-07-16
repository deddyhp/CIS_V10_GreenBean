import streamlit as st

st.set_page_config(
    page_title="Coffee Intelligence System",
    page_icon="☕",
    layout="wide",
)

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] * {
        font-size: 22px !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 28px !important;
        font-weight: bold;
    }

    .cis-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 12px;
    }

    .cis-active {
        font-weight: 700;
    }

    .cis-muted {
        opacity: 0.75;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("☕ Coffee Intelligence System")
st.caption("CIS V10.9")

st.divider()

st.markdown(
    """
    Selamat datang di **Coffee Intelligence System (CIS)**.

    Gunakan menu di sidebar untuk membuka modul CIS.
    """
)

left, right = st.columns(2)

with left:
    st.markdown(
        """
        <div class="cis-card">
            <div class="cis-active">🌱 Green Bean Database</div>
            <div class="cis-muted">Inventory dan properties green bean.</div>
        </div>

        <div class="cis-card">
            <div class="cis-active">🔥 Roast Profile</div>
            <div class="cis-muted">
                Import Artisan, Roast Database, detail profile, grafik, dan pengelolaan roast log.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="cis-card">
            <div>☕ Blend Database <span class="cis-muted">— Coming Soon</span></div>
        </div>

        <div class="cis-card">
            <div>📈 AI Roast Analysis <span class="cis-muted">— Next Phase</span></div>
            <div class="cis-muted">Fokus awal: analisis dan pembandingan Forte.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.info("👈 Pilih **Roast Profile** di sidebar untuk membuka modul.")

st.divider()

st.subheader("System Mode")

mode1, mode2 = st.columns(2)

with mode1:
    st.markdown("#### 💻 Full Mode — Laptop / Remote")
    st.write(
        "Roast Profile menggunakan database SQLite lokal di laptop, "
        "termasuk import file Artisan, penyimpanan roast log, grafik, dan edit data."
    )

with mode2:
    st.markdown("#### 📱 Fallback Mode — Tablet / HP")
    st.write(
        "CIS tetap dapat dibuka dari perangkat mobile. "
        "Fitur yang membutuhkan database lokal laptop mengikuti ketersediaan koneksi Remote."
    )

st.divider()
st.caption("© 2026 Pagerwatu Brew & Roastery")
