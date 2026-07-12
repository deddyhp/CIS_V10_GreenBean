import streamlit as st
import utils.database as db

st.set_page_config(
    page_title="Green Bean Database",
    page_icon="🌱",
    layout="wide"
)

db.create_database()

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

st.subheader("🌱 Add Green Bean")

bean_name = st.text_input("Bean Name")

species = st.selectbox(
    "Coffee Species",
    [
        "Arabica",
        "Robusta",
        "Liberica",
        "Excelsa",
        "Other"
    ]
)

origin = st.text_input("Origin")

region = st.text_input("Region")

supplier = st.text_input("Supplier")

process = st.selectbox(
    "Process",
    [
        "Washed",
        "Natural",
        "Honey",
        "Wet Hulled",
        "Anaerobic",
        "Carbonic Maceration",
        "Other"
    ]
)

variety = st.text_input("Variety")

density = st.number_input(
    "Density (g/L)",
    min_value=0.0,
    value=700.0
)

moisture = st.number_input(
    "Moisture (%)",
    min_value=0.0,
    max_value=20.0,
    value=11.0
)

stock = st.number_input(
    "Stock (kg)",
    min_value=0.0,
    value=60.0
)

location = st.text_input("Storage Location")

notes = st.text_area("Notes")

if st.button("💾 Save Green Bean"):

    db.add_greenbean(
        bean_name,
        species,
        origin,
        region,
        supplier,
        process,
        variety,
        density,
        moisture,
        stock,
        location,
        notes
    )

    st.success("✅ Green Bean berhasil disimpan.")
    
st.info("🚧 Database akan dibangun pada langkah berikutnya.")

st.divider()

st.caption("Coffee Intelligent System • V10.1")
