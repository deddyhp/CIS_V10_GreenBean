import streamlit as st
from utils.database import create_database, add_greenbean
import os

st.set_page_config(
    page_title="Green Bean Database",
    page_icon="🌱",
    layout="wide"
)

create_database()

import os

if os.path.exists("greenbean.db"):
    st.success("✅ CIS Database Ready")
else:
    st.error("❌ Database belum dibuat")

st.title("🌱 Green Bean Database")

st.divider()

st.subheader("Welcome")

st.write("""
Selamat datang di Green Bean Database.

Di sinilah seluruh data green bean Pagerwatu akan disimpan dan dikelola.
""")

st.divider()

st.subheader("Status")

st.success("✅ Green Bean Module Active")

st.divider()

st.subheader("➕ Add Green Bean")

bean_name = st.text_input("Bean Name")
origin = st.text_input("Origin")
process = st.text_input("Process")

density = st.number_input(
    "Density (g/L)",
    min_value=0.0,
    value=700.0,
    step=0.1
)

moisture = st.number_input(
    "Moisture (%)",
    min_value=0.0,
    value=11.0,
    step=0.1
)

altitude = st.number_input(
    "Altitude (masl)",
    min_value=0,
    value=1200,
    step=50
)

roast_level = st.selectbox(
    "Recommended Roast",
    [
        "Light",
        "Medium Light",
        "Medium",
        "Medium Dark"
    ]
)

if st.button("💾 Save Green Bean"):
    add_greenbean(
        bean_name,
        origin,
        process,
        density,
        moisture,
        altitude,
        roast_level
    )

    st.success("Green Bean berhasil disimpan.")
    
st.info("🚧 Database akan dibangun pada langkah berikutnya.")

st.divider()

st.caption("Coffee Intelligent System • V10.1")
