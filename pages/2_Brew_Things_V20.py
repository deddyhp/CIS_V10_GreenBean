from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

import utils.brew_database_v20 as brew_db

st.set_page_config(page_title="Brew & Things", page_icon="☕", layout="wide")

st.markdown("""
<style>
div[data-testid="stSidebarNav"] a,
div[data-testid="stSidebarNav"] span,
div[data-testid="stSidebarNav"] p {
    font-size: 22px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("☕ Brew & Things")
st.caption("Coffee Intelligence System • V20.4.1 • Brew Log Summary Fix")

try:
    brew_db.ensure_database_structure()
except Exception as exc:
    st.error(f"Koneksi Brew Things belum berhasil: {exc}")
    st.stop()

recipes = brew_db.read_sheet("Recipe_Master")
logs = brew_db.read_sheet("Brew_Log")

favorite_series = (
    recipes["Favorite"].astype(str).str.strip().str.casefold()
    if not recipes.empty else pd.Series(dtype=str)
)
log_scores = (
    pd.to_numeric(logs["Result_Score"], errors="coerce")
    if not logs.empty else pd.Series(dtype=float)
)
average_score = (
    float(log_scores.mean())
    if log_scores.notna().any() else None
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Recipes", len(recipes))
m2.metric("Brew Tests", len(logs))
m3.metric(
    "Average Score",
    f"{average_score:.2f} / 5" if average_score is not None else "-"
)
m4.metric("Favorites", int((favorite_series == "yes").sum()))

library_tab, detail_tab, new_tab, brew_log_tab, db_tab = st.tabs(
    [
        "📚 Recipe Library",
        "📖 Recipe Detail",
        "➕ New Recipe",
        "🧪 Brew Log",
        "⚙ Database",
    ]
)

with library_tab:
    st.subheader("Recipe Library")
    if recipes.empty:
        st.info("Belum ada recipe. Mulai dari tab **New Recipe**.")
    else:
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            search_text = st.text_input(
                "Search",
                placeholder="Recipe name, source, tags...",
                key="library_search",
            )

        methods = sorted(
            value for value in recipes["Brew_Method"].astype(str).unique()
            if value.strip()
        )
        statuses = sorted(
            value for value in recipes["Status"].astype(str).unique()
            if value.strip()
        )

        with c2:
            method_filter = st.selectbox(
                "Brew Method", ["All"] + methods, key="library_method"
            )
        with c3:
            status_filter = st.selectbox(
                "Status", ["All"] + statuses, key="library_status"
            )

        filtered = recipes.copy()

        if search_text.strip():
            mask = (
                filtered[["Recipe_Name", "Source", "Tags", "Purpose"]]
                .astype(str)
                .agg(" ".join, axis=1)
                .str.contains(search_text.strip(), case=False, na=False)
            )
            filtered = filtered.loc[mask]

        if method_filter != "All":
            filtered = filtered.loc[
                filtered["Brew_Method"].astype(str) == method_filter
            ]

        if status_filter != "All":
            filtered = filtered.loc[
                filtered["Status"].astype(str) == status_filter
            ]

        columns = [
            "Recipe_ID", "Recipe_Name", "Brew_Method", "Purpose",
            "Version", "Status", "Favorite", "Last_Update",
        ]
        st.dataframe(
            filtered[columns],
            use_container_width=True,
            hide_index=True,
        )

with detail_tab:
    st.subheader("Recipe Detail & Revision")

    if recipes.empty:
        st.info("Belum ada recipe yang bisa dibuka.")
    else:
        recipe_options = {
            f"{row['Recipe_ID']} — {row['Recipe_Name']}": row["Recipe_ID"]
            for _, row in recipes.iterrows()
        }

        selected_label = st.selectbox(
            "Select Recipe",
            list(recipe_options.keys()),
            key="detail_recipe",
        )
        selected_id = recipe_options[selected_label]
        recipe = brew_db.get_recipe(selected_id)

        method_options = brew_db.get_settings("Brew_Method") or [
            "V60", "Espresso", "Tubruk", "French Press", "Aeropress",
            "Kalita", "Moka Pot", "Vietnam Drip", "Cold Brew", "Others",
        ]
        ownership_options = brew_db.get_settings("Ownership") or [
            "Original", "Adapted", "Reference",
        ]
        purpose_options = brew_db.get_settings("Purpose") or [
            "Personal", "Family", "Commercial", "Experimental", "Reference",
        ]
        status_options = brew_db.get_settings("Status") or [
            "Draft", "Testing", "Approved", "Locked", "Archived",
        ]
        favorite_options = brew_db.get_settings("Favorite") or ["No", "Yes"]

        current_purposes = [
            value.strip()
            for value in str(recipe.get("Purpose", "")).split(";")
            if value.strip()
        ]

        with st.form(f"edit_recipe_{selected_id}"):
            st.markdown(f"### {selected_id}")
            left, right = st.columns(2)

            with left:
                recipe_name = st.text_input(
                    "Recipe Name *",
                    value=str(recipe.get("Recipe_Name", "")),
                )
                brew_method = st.selectbox(
                    "Brew Method",
                    method_options,
                    index=(
                        method_options.index(recipe.get("Brew_Method", ""))
                        if recipe.get("Brew_Method", "") in method_options else 0
                    ),
                )
                ownership = st.selectbox(
                    "Ownership",
                    ownership_options,
                    index=(
                        ownership_options.index(recipe.get("Ownership", ""))
                        if recipe.get("Ownership", "") in ownership_options else 0
                    ),
                )
                purposes = st.multiselect(
                    "Purpose",
                    purpose_options,
                    default=[
                        value for value in current_purposes
                        if value in purpose_options
                    ],
                )
                source = st.text_input(
                    "Source",
                    value=str(recipe.get("Source", "")),
                )
                tags = st.text_input(
                    "Tags",
                    value=str(recipe.get("Tags", "")),
                )

            with right:
                version = st.text_input(
                    "Recipe Version",
                    value=str(recipe.get("Version", "V1")),
                )
                status = st.selectbox(
                    "Status",
                    status_options,
                    index=(
                        status_options.index(recipe.get("Status", ""))
                        if recipe.get("Status", "") in status_options else 0
                    ),
                )
                favorite = st.selectbox(
                    "Favorite",
                    favorite_options,
                    index=(
                        favorite_options.index(recipe.get("Favorite", ""))
                        if recipe.get("Favorite", "") in favorite_options else 0
                    ),
                )
                bean_name = st.text_input(
                    "Bean Name",
                    value=str(recipe.get("Bean_Name", "")),
                )
                grind_setting = st.text_input(
                    "Grind Setting",
                    value=str(recipe.get("Grind_Setting", "")),
                )
                target_brew_time = st.text_input(
                    "Target Brew Time",
                    value=str(recipe.get("Target_Brew_Time", "")),
                )

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                dose_g = st.text_input(
                    "Dose (g)", value=str(recipe.get("Dose_g", ""))
                )
            with p2:
                water_g = st.text_input(
                    "Water / Yield (g)", value=str(recipe.get("Water_g", ""))
                )
            with p3:
                ratio = st.text_input(
                    "Ratio", value=str(recipe.get("Ratio", ""))
                )
            with p4:
                water_temp_c = st.text_input(
                    "Temperature (°C)",
                    value=str(recipe.get("Water_Temp_C", "")),
                )

            brewing_steps = st.text_area(
                "Brewing Steps",
                value=str(recipe.get("Brewing_Steps", "")),
                height=220,
            )

            save_revision = st.form_submit_button(
                "💾 Save Revision",
                use_container_width=True,
            )

        if save_revision:
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
        "Kalita", "Moka Pot", "Vietnam Drip", "Cold Brew", "Others",
    ]
    ownership_options = brew_db.get_settings("Ownership") or [
        "Original", "Adapted", "Reference",
    ]
    purpose_options = brew_db.get_settings("Purpose") or [
        "Personal", "Family", "Commercial", "Experimental", "Reference",
    ]
    status_options = brew_db.get_settings("Status") or [
        "Draft", "Testing", "Approved", "Locked", "Archived",
    ]
    favorite_options = brew_db.get_settings("Favorite") or ["No", "Yes"]

    with st.form("new_recipe_form", clear_on_submit=True):
        left, right = st.columns(2)

        with left:
            recipe_name = st.text_input(
                "Recipe Name *",
                placeholder="Contoh: Kenya Lemon Berry V60",
            )
            brew_method = st.selectbox("Brew Method", method_options)
            ownership = st.selectbox("Ownership", ownership_options)
            purposes = st.multiselect("Purpose", purpose_options)

        with right:
            source = st.text_input(
                "Source",
                placeholder="Deddy / Pagerwatu / sumber referensi",
            )
            version = st.text_input("Recipe Version", value="V1")
            status = st.selectbox(
                "Status",
                status_options,
                index=status_options.index("Draft")
                if "Draft" in status_options else 0,
            )
            favorite = st.selectbox(
                "Favorite",
                favorite_options,
                index=favorite_options.index("No")
                if "No" in favorite_options else 0,
            )

        tags = st.text_input(
            "Tags",
            placeholder="Kenya; Bright; Berry; Morning",
        )
        submitted = st.form_submit_button(
            "💾 Save New Recipe",
            use_container_width=True,
        )

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
        except Exception as exc:
            st.error(f"Recipe gagal disimpan: {exc}")
        else:
            st.success(f"✅ Recipe {recipe_id} berhasil disimpan.")
            st.rerun()

with brew_log_tab:
    st.subheader("Brew Test Log")

    if recipes.empty:
        st.info("Buat recipe terlebih dahulu sebelum membuat Brew Log.")
    else:
        recipe_options = {
            f"{row['Recipe_ID']} — {row['Recipe_Name']}": row["Recipe_ID"]
            for _, row in recipes.iterrows()
        }

        selected_label = st.selectbox(
            "Recipe",
            list(recipe_options.keys()),
            key="brewlog_recipe",
        )
        selected_id = recipe_options[selected_label]
        recipe = brew_db.get_recipe(selected_id) or {}

        with st.form("brew_log_form", clear_on_submit=False):
            c1, c2 = st.columns(2)

            with c1:
                log_date = st.date_input("Date", value=date.today())
                bean_name = st.text_input(
                    "Bean Used",
                    value=str(recipe.get("Bean_Name", "")),
                )
                roast_profile = st.text_input("Roast Profile")
                dose_g = st.text_input(
                    "Dose (g)",
                    value=str(recipe.get("Dose_g", "")),
                )
                water_g = st.text_input(
                    "Water / Yield (g)",
                    value=str(recipe.get("Water_g", "")),
                )

            with c2:
                ratio = st.text_input(
                    "Ratio",
                    value=str(recipe.get("Ratio", "")),
                )
                grind_setting = st.text_input(
                    "Grind Setting",
                    value=str(recipe.get("Grind_Setting", "")),
                )
                water_temp_c = st.text_input(
                    "Temperature (°C)",
                    value=str(recipe.get("Water_Temp_C", "")),
                )
                brew_time = st.text_input(
                    "Actual Brew Time",
                    placeholder="Contoh: 02:45 atau 28 sec",
                )

            st.markdown("### Sensory Score")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                aroma = st.slider("Aroma", 1.0, 5.0, 3.0, 0.5, key="score_aroma")
                sweetness = st.slider("Sweetness", 1.0, 5.0, 3.0, 0.5, key="score_sweetness")
            with s2:
                acidity = st.slider("Acidity", 1.0, 5.0, 3.0, 0.5, key="score_acidity")
                body = st.slider("Body", 1.0, 5.0, 3.0, 0.5, key="score_body")
            with s3:
                clarity = st.slider("Clarity", 1.0, 5.0, 3.0, 0.5, key="score_clarity")
                balance = st.slider("Balance", 1.0, 5.0, 3.0, 0.5, key="score_balance")
            with s4:
                aftertaste = st.slider("Aftertaste", 1.0, 5.0, 3.0, 0.5, key="score_aftertaste")

            preview_score = round(
                (
                    aroma + sweetness + acidity + body
                    + clarity + balance + aftertaste
                ) / 7,
                2,
            )
            st.metric("Automatic Overall Score", f"{preview_score:.2f} / 5")
            st.caption("Score dihitung otomatis dari 7 sensory parameters saat Save Brew Test.")

            overall_notes = st.text_area(
                "Brew Result Notes",
                placeholder=(
                    "Apa yang terasa bagus, apa yang kurang, "
                    "dan adjustment berikutnya."
                ),
                height=140,
            )

            save_log = st.form_submit_button(
                "💾 Save Brew Test",
                use_container_width=True,
            )

        if save_log:
            try:
                log_id, overall_score = brew_db.add_brew_log(
                    log_date=log_date.isoformat(),
                    recipe_id=selected_id,
                    bean_name=bean_name,
                    roast_profile=roast_profile,
                    dose_g=dose_g,
                    water_g=water_g,
                    ratio=ratio,
                    grind_setting=grind_setting,
                    water_temp_c=water_temp_c,
                    brew_time=brew_time,
                    aroma=aroma,
                    sweetness=sweetness,
                    acidity=acidity,
                    body=body,
                    clarity=clarity,
                    balance=balance,
                    aftertaste=aftertaste,
                    overall_notes=overall_notes,
                )
            except Exception as exc:
                st.error(f"Brew Log gagal disimpan: {exc}")
            else:
                st.success(
                    f"✅ {log_id} tersimpan. Overall Score: {overall_score:.2f}/5"
                )
                st.rerun()

        st.markdown("---")
        st.subheader("Brew History")

        recipe_logs = brew_db.get_brew_logs(selected_id)

        if recipe_logs.empty:
            st.info("Belum ada brew test untuk recipe ini.")
        else:
            numeric_scores = pd.to_numeric(
                recipe_logs["Result_Score"], errors="coerce"
            )
            h1, h2, h3 = st.columns(3)
            h1.metric("Total Tests", len(recipe_logs))
            h2.metric(
                "Average Score",
                f"{numeric_scores.mean():.2f}" if numeric_scores.notna().any() else "-",
            )
            h3.metric(
                "Best Score",
                f"{numeric_scores.max():.2f}" if numeric_scores.notna().any() else "-",
            )

            history_columns = [
                "Log_ID", "Date", "Bean_Name", "Roast_Profile",
                "Dose_g", "Water_g", "Ratio", "Brew_Time",
                "Result_Score", "Overall_Notes",
            ]
            st.dataframe(
                recipe_logs[history_columns].iloc[::-1],
                use_container_width=True,
                hide_index=True,
            )

with db_tab:
    st.subheader("Database Status")

    if st.button("🔄 Refresh Connection"):
        brew_db.clear_connection_cache()
        st.rerun()

    try:
        status_df = brew_db.get_database_status()
    except Exception as exc:
        st.error(
            "Google Sheets API sedang membatasi request. "
            "Tunggu sekitar satu menit lalu buka ulang tab Database."
        )
        st.caption(str(exc))
    else:
        st.dataframe(
            status_df,
            use_container_width=True,
            hide_index=True,
        )

        ready_count = int((status_df["Status"] == "Ready").sum())
        if ready_count == len(status_df):
            st.success("✅ Semua worksheet siap.")
        else:
            st.warning("Ada worksheet atau header yang belum lengkap.")
