from __future__ import annotations

import pandas as pd
import streamlit as st
import utils.brew_database_v20 as brew_db

st.set_page_config(page_title="Brew & Things", page_icon="☕", layout="wide")

st.markdown("""
<style>
div[data-testid="stSidebarNav"] a,
div[data-testid="stSidebarNav"] span,
div[data-testid="stSidebarNav"] p {font-size: 22px !important;}
</style>
""", unsafe_allow_html=True)

st.title("☕ Brew & Things")
st.caption("Coffee Intelligence System • V20.3.1 • Stability Fix")

try:
    brew_db.ensure_database_structure()
except Exception as exc:
    st.error(f"Koneksi Brew Things belum berhasil: {exc}")
    st.stop()

recipes = brew_db.read_sheet("Recipe_Master")
status_series = recipes["Status"].astype(str).str.strip() if not recipes.empty else pd.Series(dtype=str)
favorite_series = recipes["Favorite"].astype(str).str.strip().str.casefold() if not recipes.empty else pd.Series(dtype=str)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Recipes", len(recipes))
m2.metric("Testing", int((status_series == "Testing").sum()))
m3.metric("Locked", int((status_series == "Locked").sum()))
m4.metric("Favorites", int((favorite_series == "yes").sum()))

library_tab, detail_tab, new_tab, db_tab = st.tabs(
    ["📚 Recipe Library", "📖 Recipe Detail", "➕ New Recipe", "⚙ Database"]
)

with library_tab:
    st.subheader("Recipe Library")
    if recipes.empty:
        st.info("Belum ada recipe. Mulai dari tab **New Recipe**.")
    else:
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            search_text = st.text_input("Search", placeholder="Recipe name, source, tags...")
        methods = sorted(v for v in recipes["Brew_Method"].astype(str).unique() if v.strip())
        statuses = sorted(v for v in recipes["Status"].astype(str).unique() if v.strip())
        with c2:
            method_filter = st.selectbox("Brew Method", ["All"] + methods)
        with c3:
            status_filter = st.selectbox("Status", ["All"] + statuses)

        filtered = recipes.copy()
        if search_text.strip():
            mask = (
                filtered[["Recipe_Name", "Source", "Tags", "Purpose"]]
                .astype(str).agg(" ".join, axis=1)
                .str.contains(search_text.strip(), case=False, na=False)
            )
            filtered = filtered.loc[mask]
        if method_filter != "All":
            filtered = filtered.loc[filtered["Brew_Method"].astype(str) == method_filter]
        if status_filter != "All":
            filtered = filtered.loc[filtered["Status"].astype(str) == status_filter]

        columns = [
            "Recipe_ID", "Recipe_Name", "Brew_Method", "Purpose",
            "Version", "Status", "Favorite", "Last_Update"
        ]
        st.dataframe(filtered[columns], use_container_width=True, hide_index=True)
        st.caption("Buka tab Recipe Detail untuk melihat atau merevisi resep.")

with detail_tab:
    st.subheader("Recipe Detail & Revision")
    if recipes.empty:
        st.info("Belum ada recipe yang bisa dibuka.")
    else:
        options = {
            f"{row['Recipe_ID']} — {row['Recipe_Name']}": row["Recipe_ID"]
            for _, row in recipes.iterrows()
        }
        selected_label = st.selectbox("Select Recipe", list(options.keys()))
        selected_id = options[selected_label]
        recipe = brew_db.get_recipe(selected_id)

        method_options = brew_db.get_settings("Brew_Method") or [
            "V60", "Espresso", "Tubruk", "French Press", "Aeropress",
            "Kalita", "Moka Pot", "Vietnam Drip", "Cold Brew", "Others"
        ]
        ownership_options = brew_db.get_settings("Ownership") or ["Original", "Adapted", "Reference"]
        purpose_options = brew_db.get_settings("Purpose") or [
            "Personal", "Family", "Commercial", "Experimental", "Reference"
        ]
        status_options = brew_db.get_settings("Status") or [
            "Draft", "Testing", "Approved", "Locked", "Archived"
        ]
        favorite_options = brew_db.get_settings("Favorite") or ["No", "Yes"]

        current_purposes = [
            value.strip() for value in str(recipe.get("Purpose", "")).split(";") if value.strip()
        ]

        with st.form(f"edit_recipe_{selected_id}"):
            st.markdown(f"### {selected_id}")
            left, right = st.columns(2)

            with left:
                recipe_name = st.text_input("Recipe Name *", value=str(recipe.get("Recipe_Name", "")))
                brew_method = st.selectbox(
                    "Brew Method", method_options,
                    index=method_options.index(recipe.get("Brew_Method", "")) if recipe.get("Brew_Method", "") in method_options else 0
                )
                ownership = st.selectbox(
                    "Ownership", ownership_options,
                    index=ownership_options.index(recipe.get("Ownership", "")) if recipe.get("Ownership", "") in ownership_options else 0
                )
                purposes = st.multiselect(
                    "Purpose", purpose_options,
                    default=[v for v in current_purposes if v in purpose_options]
                )
                source = st.text_input("Source", value=str(recipe.get("Source", "")))
                tags = st.text_input("Tags", value=str(recipe.get("Tags", "")))

            with right:
                version = st.text_input("Recipe Version", value=str(recipe.get("Version", "V1")))
                status = st.selectbox(
                    "Status", status_options,
                    index=status_options.index(recipe.get("Status", "")) if recipe.get("Status", "") in status_options else 0
                )
                favorite = st.selectbox(
                    "Favorite", favorite_options,
                    index=favorite_options.index(recipe.get("Favorite", "")) if recipe.get("Favorite", "") in favorite_options else 0
                )
                bean_name = st.text_input("Bean Name", value=str(recipe.get("Bean_Name", "")))
                grind_setting = st.text_input("Grind Setting", value=str(recipe.get("Grind_Setting", "")))
                target_brew_time = st.text_input(
                    "Target Brew Time",
                    value=str(recipe.get("Target_Brew_Time", "")),
                    placeholder="Contoh: 02:45 atau 28 sec"
                )

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                dose_g = st.text_input("Dose (g)", value=str(recipe.get("Dose_g", "")))
            with p2:
                water_g = st.text_input("Water / Yield (g)", value=str(recipe.get("Water_g", "")))
            with p3:
                ratio = st.text_input("Ratio", value=str(recipe.get("Ratio", "")), placeholder="1:16 atau 1:2")
            with p4:
                water_temp_c = st.text_input("Temperature (°C)", value=str(recipe.get("Water_Temp_C", "")))

            brewing_steps = st.text_area(
                "Brewing Steps",
                value=str(recipe.get("Brewing_Steps", "")),
                height=220,
                placeholder=(
                    "0:00 — Bloom 45 g\n"
                    "0:40 — Pour to 120 g\n"
                    "1:15 — Pour to 180 g\n"
                    "1:50 — Final pour to 240 g"
                )
            )

            save_revision = st.form_submit_button("💾 Save Revision", use_container_width=True)

        if save_revision:
            if not recipe_name.strip():
                st.warning("Recipe Name wajib diisi.")
            else:
                try:
                    brew_db.update_recipe(
                        selected_id,
                        {
                            "Recipe_Name": recipe_name.strip(),
                            "Brew_Method": brew_method,
                            "Ownership": ownership,
                            "Purpose": "; ".join(purposes),
                            "Source": source.strip(),
                            "Version": version.strip() or "V1",
                            "Status": status,
                            "Favorite": favorite,
                            "Tags": tags.strip(),
                            "Bean_Name": bean_name.strip(),
                            "Dose_g": dose_g.strip(),
                            "Water_g": water_g.strip(),
                            "Ratio": ratio.strip(),
                            "Grind_Setting": grind_setting.strip(),
                            "Water_Temp_C": water_temp_c.strip(),
                            "Target_Brew_Time": target_brew_time.strip(),
                            "Brewing_Steps": brewing_steps.strip(),
                        },
                    )
                except Exception as exc:
                    st.error(f"Revision gagal disimpan: {exc}")
                else:
                    st.success(f"✅ Recipe {selected_id} berhasil direvisi.")
                    st.rerun()

with new_tab:
    st.subheader("Create New Recipe")
    method_options = brew_db.get_settings("Brew_Method") or [
        "V60", "Espresso", "Tubruk", "French Press", "Aeropress",
        "Kalita", "Moka Pot", "Vietnam Drip", "Cold Brew", "Others"
    ]
    ownership_options = brew_db.get_settings("Ownership") or ["Original", "Adapted", "Reference"]
    purpose_options = brew_db.get_settings("Purpose") or [
        "Personal", "Family", "Commercial", "Experimental", "Reference"
    ]
    status_options = brew_db.get_settings("Status") or [
        "Draft", "Testing", "Approved", "Locked", "Archived"
    ]
    favorite_options = brew_db.get_settings("Favorite") or ["No", "Yes"]

    with st.form("new_recipe_form", clear_on_submit=True):
        left, right = st.columns(2)
        with left:
            recipe_name = st.text_input("Recipe Name *", placeholder="Contoh: Kenya Lemon Berry V60")
            brew_method = st.selectbox("Brew Method", method_options)
            ownership = st.selectbox("Ownership", ownership_options)
            purposes = st.multiselect("Purpose", purpose_options)
        with right:
            source = st.text_input("Source", placeholder="Deddy / Pagerwatu / sumber referensi")
            version = st.text_input("Recipe Version", value="V1")
            status = st.selectbox("Status", status_options, index=status_options.index("Draft") if "Draft" in status_options else 0)
            favorite = st.selectbox("Favorite", favorite_options, index=favorite_options.index("No") if "No" in favorite_options else 0)

        tags = st.text_input("Tags", placeholder="Kenya; Bright; Berry; Morning")
        submitted = st.form_submit_button("💾 Save New Recipe", use_container_width=True)

    if submitted:
        try:
            recipe_id = brew_db.add_recipe(
                recipe_name=recipe_name,
                brew_method=brew_method,
                ownership=ownership,
                purposes=purposes,
                source=source,
                version=version,
                status=status,
                favorite=favorite,
                tags=tags,
            )
        except ValueError as exc:
            st.warning(str(exc))
        except Exception as exc:
            st.error(f"Recipe gagal disimpan: {exc}")
        else:
            st.success(f"✅ Recipe {recipe_id} berhasil disimpan.")
            st.rerun()

with db_tab:
    st.subheader("Database Status")
    if st.button("🔄 Refresh Connection"):
        brew_db.clear_connection_cache()
        st.rerun()

    status_df = brew_db.get_database_status()
    st.dataframe(status_df, use_container_width=True, hide_index=True)

    ready_count = int((status_df["Status"] == "Ready").sum())
    if ready_count == len(status_df):
        st.success("✅ Semua worksheet siap.")
    else:
        st.warning("Ada worksheet atau header yang belum lengkap.")
