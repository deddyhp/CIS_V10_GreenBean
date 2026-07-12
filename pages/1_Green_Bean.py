import streamlit as st
import utils.database as db

st.set_page_config(page_title="Green Bean", page_icon="🌱", layout="wide")

db.create_database()

st.title("🌱 Green Bean Database")
st.caption("Coffee Intelligent System • V10.5")

st.divider()

st.subheader("🆕 Version History")

st.markdown("""
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

st.subheader("➕ Add New Green Bean")

bean_name = st.text_input("Bean Name")

species = st.selectbox(
    "Coffee Species",
    ["Arabica","Robusta","Liberica","Excelsa","Other"]
)

origin = st.text_input("Origin")
region = st.text_input("Region")
supplier = st.text_input("Supplier")
process = st.text_input("Process")
variety = st.text_input("Variety")

density = st.number_input("Density (g/L)",0.0)
moisture = st.number_input("Moisture (%)",0.0)
stock = st.number_input("Stock (kg)",0.0)

location = st.text_input("Storage Location")
notes = st.text_area("Notes")

if st.button("💾 Save Green Bean"):
    db.add_greenbean(
        bean_name,species,origin,region,supplier,
        process,variety,density,moisture,
        stock,location,notes
    )
    st.success("✅ Green Bean berhasil disimpan.")

st.divider()

st.subheader("📥 BP2 Import")
st.info("🚧 Coming Soon")

st.divider()

st.subheader("🔍 Green Bean Explorer")

keyword = st.text_input(
    "Search",
    placeholder="Bean / Origin / Species / Process"
)

if keyword.strip():
    df = db.search_greenbean(keyword)
else:
    df = db.get_all_greenbean()

st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(f"Total Bean : {len(df)}")
