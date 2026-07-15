import inspect
import streamlit as st
import utils.database as db

st.set_page_config(page_title="Green Bean", page_icon="🌱", layout="wide")

# Keep the default Streamlit multipage navigation and enlarge its font only.
st.markdown("""
<style>
div[data-testid="stSidebarNav"] a,
div[data-testid="stSidebarNav"] span,
div[data-testid="stSidebarNav"] p {
    font-size: 22px !important;
}
</style>
""", unsafe_allow_html=True)

try:
    db.create_database()
except Exception as exc:
    st.error(f"Koneksi Google Sheets belum siap: {exc}")
    st.stop()

st.title("🌱 Green Bean Database")
st.caption("Coffee Intelligent System • V10.9")

st.divider()

with st.expander("➕ Add New Green Bean"):
    with st.form("add_greenbean_form", clear_on_submit=True):
        bean_name = st.text_input("Bean Name")
        species = st.selectbox(
            "Coffee Species",
            ["Arabica", "Robusta", "Liberica", "Excelsa", "Other"],
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
            acquisition_price_per_kg = st.number_input(
                "Acquisition Price / kg (Rp)",
                min_value=0.0,
                step=1000.0,
                format="%.0f",
            )

        notes = st.text_area("Notes")
        save_new = st.form_submit_button("💾 Save Green Bean", type="primary")

        if save_new:
            if not bean_name.strip():
                st.error("Bean Name wajib diisi.")
            else:
                try:
                    add_signature = inspect.signature(db.add_greenbean)
                    add_parameter_count = len(add_signature.parameters)

                    if add_parameter_count >= 13:
                        bean_id = db.add_greenbean(
                            bean_name.strip(),
                            species,
                            origin.strip(),
                            region.strip(),
                            supplier.strip(),
                            process.strip(),
                            variety.strip(),
                            density,
                            moisture,
                            stock,
                            acquisition_price_per_kg,
                            location.strip(),
                            notes.strip(),
                        )
                    else:
                        # Compatibility mode for runtimes still exposing
                        # the V10.8 12-argument add_greenbean function.
                        bean_id = db.add_greenbean(
                            bean_name.strip(),
                            species,
                            origin.strip(),
                            region.strip(),
                            supplier.strip(),
                            process.strip(),
                            variety.strip(),
                            density,
                            moisture,
                            stock,
                            location.strip(),
                            notes.strip(),
                        )

                        row_number = db._find_row_number(bean_id)
                        if row_number is None:
                            raise ValueError(
                                f"Bean ID {bean_id} tidak ditemukan setelah disimpan."
                            )
                        worksheet = db._get_worksheet()
                        worksheet.update(
                            f"S{row_number}",
                            [[float(acquisition_price_per_kg)]],
                            value_input_option="USER_ENTERED",
                        )

                    st.success(
                        f"✅ Green Bean {bean_id} dan harga perolehan berhasil disimpan."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Green Bean gagal disimpan: {exc}")

st.divider()
st.subheader("📦 Green Bean Inventory")

keyword = st.text_input(
    "Search",
    placeholder="Bean / Origin / Species / Process / Bean ID",
)

try:
    df = db.search_greenbean(keyword.strip()) if keyword.strip() else db.get_all_greenbean()
except Exception as exc:
    st.error(f"Database gagal dibaca: {exc}")
    st.stop()

# Migration-safe fallback:
# Some runtimes may still expose the V10.8 dataframe schema and drop
# the V10.9 price column. In that case, read the price directly from
# the active Google Sheet and merge it back by bean_id.
if "acquisition_price_per_kg" not in df.columns:
    df["acquisition_price_per_kg"] = 0.0
    try:
        worksheet = db._get_worksheet()
        sheet_records = worksheet.get_all_records(default_blank="")
        price_map = {
            str(record.get("bean_id", "")): float(
                record.get("acquisition_price_per_kg", 0) or 0
            )
            for record in sheet_records
        }
        df["acquisition_price_per_kg"] = (
            df["bean_id"].astype(str).map(price_map).fillna(0.0)
        )
    except Exception:
        # Keep Rp0 only when the sheet price cannot be read.
        pass

if df.empty:
    st.info("Belum ada Green Bean yang ditemukan di Google Sheets.")
else:
    stock_display = df[[
        "bean_id", "bean_name", "species", "origin", "process",
        "stock", "acquisition_price_per_kg", "location"
    ]].copy()
    stock_display["stock_value"] = (
        stock_display["stock"].astype(float)
        * stock_display["acquisition_price_per_kg"].astype(float)
    )

    # Put calculated stock value before location so displayed headers
    # always match the underlying data columns.
    stock_display = stock_display[[
        "bean_id", "bean_name", "species", "origin", "process",
        "stock", "acquisition_price_per_kg", "stock_value", "location"
    ]]
    stock_display.columns = [
        "Bean ID", "Bean Name", "Species", "Origin", "Process",
        "Stock (kg)", "Acquisition Price / kg (Rp)", "Stock Value (Rp)", "Location"
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
        placeholder="Klik lalu pilih salah satu bean",
    )

    if selected_label:
        selected_bean_id = bean_options[selected_label]
        bean = db.get_greenbean_by_bean_id(selected_bean_id)

        if bean:
            # Keep V10.9 price available even when get_greenbean_by_bean_id()
            # is still backed by the older V10.8 dataframe schema.
            selected_row = df[
                df["bean_id"].astype(str) == str(selected_bean_id)
            ]
            if not selected_row.empty:
                bean["acquisition_price_per_kg"] = float(
                    selected_row.iloc[0].get("acquisition_price_per_kg", 0) or 0
                )

            st.divider()
            st.subheader(f"🌱 {bean['bean_name']}")
            st.caption(f"Bean ID: {bean['bean_id']}")

            stock_value = (
                float(bean.get("stock") or 0)
                * float(bean.get("acquisition_price_per_kg") or 0)
            )

            metric1, metric2, metric3, metric4 = st.columns(4)
            metric1.metric("Remaining Stock", f"{float(bean['stock'] or 0):.2f} kg")
            metric2.metric(
                "Acquisition Price / kg",
                f"Rp {float(bean.get('acquisition_price_per_kg') or 0):,.0f}",
            )
            metric3.metric("Remaining Stock Value", f"Rp {stock_value:,.0f}")
            metric4.metric("Species", bean.get("species") or "-")

            info_tab, edit_tab, stock_tab = st.tabs([
                "📋 Properties",
                "✏️ Edit Properties",
                "⚖️ Stock Adjustment",
            ])

            with info_tab:
                left, right = st.columns(2)
                with left:
                    st.markdown(f"**Origin:** {bean.get('origin') or '-'}")
                    st.markdown(f"**Region:** {bean.get('region') or '-'}")
                    st.markdown(f"**Supplier:** {bean.get('supplier') or '-'}")
                    st.markdown(f"**Variety:** {bean.get('variety') or '-'}")
                with right:
                    st.markdown(f"**Density:** {float(bean.get('density') or 0):.1f} g/L")
                    st.markdown(f"**Moisture:** {float(bean.get('moisture') or 0):.1f}%")
                    st.markdown(f"**Storage Location:** {bean.get('location') or '-'}")
                    st.markdown(
                        f"**Acquisition Price / kg:** "
                        f"Rp {float(bean.get('acquisition_price_per_kg') or 0):,.0f}"
                    )
                    st.markdown(f"**Created:** {bean.get('created_at') or '-'}")
                    st.markdown(f"**Last Updated:** {bean.get('updated_at') or '-'}")

                st.markdown("**Notes**")
                st.info(bean.get("notes") or "Tidak ada catatan.")

                st.markdown("#### 🕘 Last Stock Update")
                history1, history2, history3 = st.columns(3)
                history1.metric(
                    "Previous Stock",
                    f"{float(bean.get('last_stock_before') or 0):.2f} kg",
                )
                history2.metric("Remark", bean.get("last_stock_remark") or "-")
                history3.metric("Updated At", bean.get("last_stock_updated_at") or "-")

            with edit_tab:
                with st.form(f"edit_properties_{selected_bean_id}"):
                    edit_name = st.text_input("Bean Name", value=str(bean.get("bean_name") or ""))
                    species_options = ["Arabica", "Robusta", "Liberica", "Excelsa", "Other"]
                    current_species = bean.get("species") or "Other"
                    species_index = species_options.index(current_species) if current_species in species_options else 4
                    edit_species = st.selectbox("Coffee Species", species_options, index=species_index)

                    e1, e2 = st.columns(2)
                    with e1:
                        edit_origin = st.text_input("Origin", value=str(bean.get("origin") or ""))
                        edit_supplier = st.text_input("Supplier", value=str(bean.get("supplier") or ""))
                        edit_variety = st.text_input("Variety", value=str(bean.get("variety") or ""))
                        edit_moisture = st.number_input(
                            "Moisture (%)",
                            min_value=0.0,
                            value=float(bean.get("moisture") or 0),
                            step=0.1,
                        )
                        edit_location = st.text_input(
                            "Storage Location",
                            value=str(bean.get("location") or ""),
                        )
                    with e2:
                        edit_region = st.text_input("Region", value=str(bean.get("region") or ""))
                        edit_process = st.text_input("Process", value=str(bean.get("process") or ""))
                        edit_density = st.number_input(
                            "Density (g/L)",
                            min_value=0.0,
                            value=float(bean.get("density") or 0),
                            step=0.1,
                        )
                        edit_acquisition_price_per_kg = st.number_input(
                            "Acquisition Price / kg (Rp)",
                            min_value=0.0,
                            value=float(bean.get("acquisition_price_per_kg") or 0),
                            step=1000.0,
                            format="%.0f",
                        )

                    edit_notes = st.text_area("Notes", value=str(bean.get("notes") or ""))
                    save_properties = st.form_submit_button("💾 Save Properties", type="primary")

                    if save_properties:
                        if not edit_name.strip():
                            st.error("Bean Name wajib diisi.")
                        else:
                            try:
                                update_signature = inspect.signature(
                                    db.update_greenbean_properties
                                )
                                update_parameter_count = len(update_signature.parameters)

                                if update_parameter_count >= 13:
                                    # Native V10.9 database function.
                                    db.update_greenbean_properties(
                                        selected_bean_id,
                                        edit_name.strip(),
                                        edit_species,
                                        edit_origin.strip(),
                                        edit_region.strip(),
                                        edit_supplier.strip(),
                                        edit_process.strip(),
                                        edit_variety.strip(),
                                        edit_density,
                                        edit_moisture,
                                        edit_acquisition_price_per_kg,
                                        edit_location.strip(),
                                        edit_notes.strip(),
                                    )
                                else:
                                    # Compatibility mode for a Streamlit runtime
                                    # that still exposes the V10.8 12-argument function.
                                    db.update_greenbean_properties(
                                        selected_bean_id,
                                        edit_name.strip(),
                                        edit_species,
                                        edit_origin.strip(),
                                        edit_region.strip(),
                                        edit_supplier.strip(),
                                        edit_process.strip(),
                                        edit_variety.strip(),
                                        edit_density,
                                        edit_moisture,
                                        edit_location.strip(),
                                        edit_notes.strip(),
                                    )

                                    row_number = db._find_row_number(selected_bean_id)
                                    if row_number is None:
                                        raise ValueError(
                                            f"Bean ID {selected_bean_id} tidak ditemukan."
                                        )
                                    worksheet = db._get_worksheet()
                                    worksheet.update(
                                        f"S{row_number}",
                                        [[float(edit_acquisition_price_per_kg)]],
                                        value_input_option="USER_ENTERED",
                                    )

                                st.success("✅ Bean properties dan harga berhasil diperbarui.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Properties gagal diperbarui: {exc}")

            with stock_tab:
                with st.form(f"stock_form_{selected_bean_id}"):
                    new_stock = st.number_input(
                        "New Remaining Stock (kg)",
                        min_value=0.0,
                        value=float(bean.get("stock") or 0),
                        step=0.1,
                        format="%.2f",
                    )
                    stock_reason = st.selectbox(
                        "Adjustment Reason",
                        ["Roasting", "Purchase", "Sample", "Waste", "Stock Correction", "Other"],
                    )
                    stock_note = st.text_input(
                        "Remark",
                        placeholder="Contoh: Roast batch 500 g atau koreksi hasil timbang",
                    )
                    save_stock = st.form_submit_button("💾 Save Stock Adjustment", type="primary")

                    if save_stock:
                        final_remark = stock_reason if not stock_note.strip() else f"{stock_reason} — {stock_note.strip()}"
                        try:
                            db.update_greenbean_stock(selected_bean_id, new_stock, final_remark)
                            st.success(
                                f"✅ Stock {selected_bean_id} diperbarui menjadi {new_stock:.2f} kg."
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Stock gagal diperbarui: {exc}")

st.caption(f"Total Bean: {len(df)}")
