import streamlit as st

st.set_page_config(
    page_title="Green Bean Database",
    page_icon="🌱",
    layout="wide"
)

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

st.info("🚧 Database akan dibangun pada langkah berikutnya.")

st.divider()

st.caption("Coffee Intelligent System • V10.1")
