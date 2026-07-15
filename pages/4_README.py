import streamlit as st


st.set_page_config(
    page_title="CIS README",
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
        max-width: 1100px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    hr {
        margin-top: 1.2rem;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📖 CIS README")
st.caption("Coffee Intelligence System • Project Overview & Release Notes")
st.divider()

st.markdown(
    """
## Coffee Intelligence System

**CIS** adalah coffee database tools yang mendukung perjalanan kopi dari bahan baku hingga hasil seduh.

> **Green Bean → Roast Profile → Brew Things → Analyze → Improve**

CIS menyimpan fakta, riwayat, dan hasil kerja.  
Chaty membantu sebagai programmer, system architect, analytical assistant, dan advisor.  
Deddy tetap menjadi project owner dan engineer.

---

## Three Core Databases

### 🌱 Green Bean

**Fokus utama:**

- Green bean inventory
- Stock in dan stock out
- Remaining stock
- Bean properties dan storage location
- Structured AI output untuk dianalisis bersama Chaty

**Current stable utilization version: V10.8**

**Status saat ini:**

- Google Sheets cloud database
- Add dan edit bean properties
- Stock adjustment dengan remark
- Inventory search dan update history
- Sedang memasuki real-world utilization dan pengisian database

---

### 🔥 Roast Profile

**Fokus utama:**

- Database seluruh hasil roasting
- Import dan penyimpanan roast profile
- Membuka kembali roast log
- Roast analytics dan perbandingan batch
- Structured AI output untuk dianalisis bersama Chaty

**Current stable database version: V04.4**

**Status saat ini:**

- Import roast berhasil
- Roast database berjalan baik
- Semua data roast dapat disimpan dan dibuka kembali
- Fondasi database sudah perfect
- Advanced analytics dan AI support menjadi fase berikutnya

---

### ☕ Brew Things

**Fokus utama:**

- Brew Recipe
- Favorite Recipe
- Lab & Trial Recipe
- Catatan hasil seduh
- Advice Chaty sebagai bagian dari trial dan improvement

**Current stable version: V20.4.1**

**Status saat ini:**

- Struktur Brew Things sudah berjalan
- Favorite dan Lab & Trial menjadi bagian utama
- Pengembangan selanjutnya mengikuti hasil penggunaan nyata

---

## Project Target

Setiap modul CIS dikembangkan dengan alur:

> **Build → Real Data Input → Utilization → HVPT → Running Smooth → Advanced**

**HVPT** berarti **High Volume Production Test**.

Fokus utama bukan menambah fitur sebanyak-banyaknya, tetapi memastikan setiap modul:

- Stabil
- Nyaman digunakan
- Aman untuk data nyata
- Berjalan smooth pada pemakaian rutin
- Siap menjadi fondasi analisis AI

---

## Three-Device Architecture

### 💻 Laptop

- Support device untuk roasting
- Menangani roasting data
- Tempat utama database dan file operasional
- Digunakan untuk proses yang lebih berat

### 📱 Samsung Galaxy Tab S9+

- Main CIS device
- Diskusi utama dengan Chaty
- Project development
- Review, analysis, dan decision making

### 📲 Samsung Galaxy S23+

- Mobile support device
- Sudden idea dan quick analysis
- Input cepat Green Bean dan Brew Things
- Pendamping tablet ketika sangat mobile

---

## Development Principles

### Simple, Flexible, Sustainable

Setiap keputusan CIS harus menjaga sistem tetap:

- **Simple** untuk digunakan
- **Flexible** antar-device dan kebutuhan
- **Sustainable** untuk perkembangan jangka panjang

### Version Discipline

- Maksimal sekitar **5 achievement version per chat**
- Setelah itu pindah ke chat baru
- Saat pindah, bawa versi locked, keputusan penting, bug terbuka, dan next step
- Satu versi coding diberikan sebagai **full downloadable script**
- Patching kecil hanya dilakukan jika diminta khusus
- Screenshot dipakai untuk validasi, bukan untuk copas kode panjang

---

## Release Notes

### Green Bean

#### V10.8 — Stable Utilization

- Google Sheets cloud database
- Edit bean properties
- Stock adjustment remark
- Update history information

#### V10.7

- Bigger sidebar menu font
- Default Streamlit navigation dipertahankan

#### V10.6

- Simple inventory view
- Open bean properties from stock list
- Update remaining stock

---

### Roast Profile

#### V04.4 — Stable Database

- Import roast berhasil
- Roast log database berjalan
- Data roast dapat dibuka kembali
- Fondasi database siap untuk utilization

---

### Brew Things

#### V20.4.1 — Stable Improvement

- Minor refinement setelah V20.4
- Struktur database dan penggunaan tetap dipertahankan

#### V20.4 — Stable Achievement

- Brew Things core structure
- Favorite Recipe
- Lab & Trial Recipe
- Fondasi pencatatan advice dan improvement

---

## Long-Term Vision

CIS bukan database mati.

CIS adalah **Coffee Intelligence System** yang belajar dari pengalaman nyata Deddy sendiri:

- Bean yang dibeli dan disimpan
- Cara setiap bean di-roast
- Hasil rasa di dalam cangkir
- Trial yang gagal maupun berhasil
- Analisis dan advice dari Chaty
- Keputusan improvement berikutnya

> **CIS menyimpan pengalaman. Chaty membantu mengubahnya menjadi insight.**
"""
)

st.divider()
st.caption("CIS Homepage • Global Project Reference")
