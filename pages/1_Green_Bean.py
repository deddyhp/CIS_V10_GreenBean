import streamlit as st
import utils.database as db

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

db.create_database()

# ---------- Custom CSS ----------
st.markdown("""
<style>
/* Hide default Streamlit multipage navigation so we can use a cleaner custom sidebar */
div[data-testid="stSidebarNav"] {
    display: none;
}

/* Sidebar menu styling */
section[data-testid="stSidebar"] .sidebar-home-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 8px;
}

section[data-testid="stSidebar"] .sidebar-home-box {
    font-size: 22px;
    font-weight: 700;
    background: #F3F5F9;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 6px;
    margin-bottom: 14px;
    border-left: 5px solid #5E9D64;
}

section[data-testid="stSidebar"] .sidebar-caption {
    font-size: 14px;
    color: #666666;
    margin-top: 10px;
    line-height: 1.4;
}
</style>
""", unsafe_allow_html=True)

# ---------- Custom Sidebar ----------
with st.sidebar:
    st.markdown('<div class="sidebar-home-title">🏠 Menu</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-home-box">🌱 Home</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-caption">Green Bean Database is now under the Home menu. '
        'Ready to be combined with future CIS features.</div>',
        unsafe_allow_html=True,
    )

# ---------- Main Page ----------
st.title("🌱 Green Bean Database")
st.caption("Coffee Intelligent System • V10.7")

st.divider()

st.subheader("🆕 Version History")

st.markdown("""
### V10.7
- 🏠 Sidebar Home Menu
- 🔠 Sidebar Menu Font 22
- ✨ Cleaner Navigation Identity

### V10.6
- 📦 Simple Inventory View
- 👆 Open Bean Properties from Stock List
- ⚖️ Update Remaining Stock

### V10.5
- 🔍 Green Bean Explorer
- 📋 Search Database
- 📊 Total Bean Counter

### V10.4
- 📚 Green Bean Explorer Foundation
- 📥 BP2 Import Planning

### V10.3
- 👓 Bigger Sidebar Font

### V10.2
- 🌱 Coffee Species
- 🆔 Automatic Bean ID

### V10.1
- 🚀 Initial Green Bean Module
""")

st.divider()

with st.expander("➕ Add New Green Bean"):
    with st.form("add_greenbean_form", clear_on_submit=True):
        bean_name = st.text_input("Bean Name")

        species = st.selectbox(
            "Coffee Species",
            ["Arabica", "Robusta", "Liberica", "Excelsa", "Other"]
        )

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("Origin")
            supplier = st.text_input("Supplier")
            variety = st.text_input("Variety")
            moisture = st.number_input("Moisture (%)", min_value=0.0, step=0.1)
            location = st.text_input("Storage Location")

        with col2:
            region = st.text_input("Region")
            process = st.text_input("Process")
            density = st.number_input("Density (g/L)", min_value=0.0, step=0.1)
            stock = st.number_input("Initial Stock (kg)", min_value=0.0, step=0.1)

        notes = st.text_area("Notes")

        save_new = st.form_submit_button("💾 Save Green Bean", type="primary")

        if save_new:
            if not bean_name.strip():
                st.error("Bean Name wajib diisi.")
            else:
                try:
                    bean_id = db.add_greenbean(
                        bean_name.strip(), species, origin.strip(), region.strip(),
                        supplier.strip(), process.strip(), variety.strip(), density,
                        moisture, stock, location.strip(), notes.strip()
                    )
                    st.success(f"✅ Green Bean {bean_id} berhasil disimpan.")
                except Exception as exc:
                    st.error(f"Green Bean gagal disimpan: {exc}")

st.divider()

st.subheader("📦 Green Bean Inventory")

keyword = st.text_input(
    "Search",
    placeholder="Bean / Origin / Species / Process / Bean ID"
)

if keyword.strip():
    df = db.search_greenbean(keyword.strip())
else:
    df = db.get_all_greenbean()

if df.empty:
    st.info("Belum ada Green Bean yang ditemukan.")
else:
    stock_display = df[["bean_id", "bean_name", "species", "origin", "process", "stock", "location"]].copy()
    stock_display.columns = [
        "Bean ID", "Bean Name", "Species", "Origin", "Process", "Stock (kg)", "Location"
    ]
    st.dataframe(stock_display, use_container_width=True, hide_index=True)

    bean_options = {
        f"{row['bean_id']} • {row['bean_name']} • Stock {float(row['stock'] or 0):.2f} kg": row["bean_id"]
        for _, row in df.iterrows()
    }

    selected_label = st.selectbox(
        "Pilih bean untuk membuka properties",
        options=list(bean_options.keys()),
        index=None,
        placeholder="Klik lalu pilih salah satu bean"
    )

    if selected_label:
        selected_bean_id = bean_options[selected_label]
        bean = db.get_greenbean_by_bean_id(selected_bean_id)

        if bean:
            st.divider()
            st.subheader(f"🌱 {bean['bean_name']}")
            st.caption(f"Bean ID: {bean['bean_id']}")

            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Remaining Stock", f"{float(bean['stock'] or 0):.2f} kg")
            metric2.metric("Species", bean['species'] or "-")
            metric3.metric("Process", bean['process'] or "-")

            left, right = st.columns(2)
            with left:
                st.markdown(f"**Origin:** {bean['origin'] or '-'}")
                st.markdown(f"**Region:** {bean['region'] or '-'}")
                st.markdown(f"**Supplier:** {bean['supplier'] or '-'}")
                st.markdown(f"**Variety:** {bean['variety'] or '-'}")
            with right:
                density_text = f"{float(bean['density']):.1f} g/L" if bean['density'] is not None else "-"
                moisture_text = f"{float(bean['moisture']):.1f}%" if bean['moisture'] is not None else "-"
                st.markdown(f"**Density:** {density_text}")
                st.markdown(f"**Moisture:** {moisture_text}")
                st.markdown(f"**Storage Location:** {bean['location'] or '-'}")
                st.markdown(f"**Last Updated:** {bean['updated_at'] or '-'}")

            st.markdown("**Notes**")
            st.info(bean['notes'] or "Tidak ada catatan.")

            with st.form(f"stock_form_{selected_bean_id}"):
                new_stock = st.number_input(
                    "Update Remaining Stock (kg)",
                    min_value=0.0,
                    value=float(bean['stock'] or 0),
                    step=0.1,
                    format="%.2f"
                )
                save_stock = st.form_submit_button("💾 Save Stock", type="primary")

                if save_stock:
                    try:
                        db.update_greenbean_stock(selected_bean_id, new_stock)
                        st.success(f"✅ Stock {selected_bean_id} diperbarui menjadi {new_stock:.2f} kg.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Stock gagal diperbarui: {exc}")

st.caption(f"Total Bean: {len(df)}")
