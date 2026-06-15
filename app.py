import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# ==============================================================================
# 1. KONFIGURASI HALAMAN UTAMA STREAMLIT (Harus berada di baris paling atas)
# ==============================================================================
st.set_page_config(
    page_title="Data Pelamar TIK Sekolah Rakyat", page_icon="📊", layout="wide"
)

# ==============================================================================
# 2. INJECT CSS CUSTOM (Untuk Meratakan Tengah Teks Metrik)
# ==============================================================================
st.markdown(
    """
    <style>
    /* Memaksa elemen label, nilai, dan delta pada st.metric agar rata tengah */
    [data-testid="stMetricValue"], 
    [data-testid="stMetricLabel"], 
    [data-testid="stMetricDelta"] {
        text-align: center;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. HEADER / JUDUL APLIKASI
# ==============================================================================
st.markdown(
    "<h1 style='text-align: center; color: #1E3A8A;'>📊 Data Pelamar TIK Sekolah Rakyat</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #6B7280; font-size: 1.2rem;'>Dashboard Pemantauan Formasi dan Keketatan Pelamar Berdasarkan Wilayah</p>",
    unsafe_allow_html=True,
)
st.write("---")


# ==============================================================================
# 4. FUNGSI PEMROSESAN DATA (REKAP)
# ==============================================================================
def rekap(df: pd.DataFrame) -> pd.DataFrame:
    # Ekstrak Wilayah
    df[["provinsi", "kota", "formasi"]] = (
        df["Wilayah Yang Dipilih"].str.strip()
    ).str.split(" - ", expand=True)
    df = df.drop(columns=["Wilayah Yang Dipilih", "Timestamp"])

    # Edit kolom provinsi dan formasi menggunakan Regex
    df["provinsi"] = df["provinsi"].str.replace(
        r"[^a-zA-Z]+", "", regex=True
    )
    df["formasi"] = (
        df["formasi"].str.replace(r"\D+", "", regex=True).astype(int)
    )

    # Melakukan Groupby dan Agregasi
    rekap_df = df.groupby(["provinsi", "kota"]).agg(
        pelamar=("kota", "count"), formasi=("formasi", "first")
    )

    # Menghitung Persentase Keketatan
    rekap_df["persentase"] = (
        rekap_df["pelamar"] / rekap_df["formasi"] * 100
    ).round(2)

    return rekap_df.sort_values(by="persentase", ascending=False)


# ==============================================================================
# 5. LOAD DATA DENGAN CACHING
# ==============================================================================
@st.cache_data(ttl=600)  # Cache data selama 10 menit (600 detik)
def load_data():
    link_sheet = "https://docs.google.com/spreadsheets/d/1VX1Rk_WjyGVx3AiOlsocMRB5xRT0R8T85RP6c4j7Xh0/export?format=csv&gdid=0"
    df_raw = pd.read_csv(link_sheet)
    return rekap(df_raw)


# ==============================================================================
# 6. LOGIKA UTAMA DASHBOARD
# ==============================================================================
try:
    # Memuat data yang sudah bersih
    cek = load_data()

    # Mengambil list nama provinsi unik dari MultiIndex level 0
    list_provinsi = cek.index.get_level_values("provinsi").unique().sort_values()

    # Membuat Sidebar untuk filter pilihan Provinsi
    st.sidebar.header("⚙️ Filter Wilayah")
    pilihan_provinsi = st.sidebar.selectbox(
        "Pilih Provinsi:", list_provinsi
    )

    # Melakukan filter data (cross-section) mirip df.loc
    data_filter = cek.xs(pilihan_provinsi, level="provinsi")

    # --------------------------------------------------------------------------
    # BAGIAN RINGKASAN DATA (METRICS) - Support 2 Baris 2 Kolom di HP + Rata Tengah
    # --------------------------------------------------------------------------
    st.subheader(f"📍 Ringkasan - Provinsi {pilihan_provinsi}")

    # Kalkulasi nilai ringkasan
    total_kota = len(data_filter)
    total_pelamar = data_filter["pelamar"].sum()
    total_formasi = data_filter["formasi"].sum()
    rata_persentase = (total_pelamar / total_formasi * 100).round(2)

    # Baris Pertama Metrik (Kolom 1 & 2)
    row1_col1, row1_col2 = st.columns(2, gap="medium")
    with row1_col1:
        st.metric(label="Total Kota/Kab", value=f"{total_kota} Wilayah")
    with row1_col2:
        st.metric(label="Total Pelamar", value=f"{total_pelamar} Orang")

    # Baris Kedua Metrik (Kolom 3 & 4)
    row2_col1, row2_col2 = st.columns(2, gap="medium")
    with row2_col1:
        st.metric(label="Total Formasi", value=f"{total_formasi} Slot")
    with row2_col2:
        st.metric(
            label="Rata-rata Keketatan",
            value=f"{rata_persentase}%",
            delta="Overcapacity" if rata_persentase > 100 else "Normal",
        )

    st.write("---")

    # --------------------------------------------------------------------------
    # BAGIAN TABEL DATA & GRAFIK VISUALISASI (LAYOUT KANAN-KIRI)
    # --------------------------------------------------------------------------
    col_tabel, col_grafik = st.columns([1, 1], gap="large")

    # Kolom Kiri: Tabel Data
    with col_tabel:
        st.subheader("📋 Tabel Detail Wilayah")
        # Menampilkan data dengan gradasi warna biru pada kolom persentase
        st.dataframe(
            data_filter.style.background_gradient(
                cmap="magma", subset=["persentase"]
            ),
            use_container_width=True
        )

    # Kolom Kanan: Grafik Batang
    with col_grafik:
        st.subheader("📊 Grafik Keketatan (%) per Kota")

        # Membuat canvas grafik menggunakan Matplotlib & Seaborn
        fig, ax = plt.subplots(figsize=(6, 4)) if len(data_filter.index.tolist()) < 5 else plt.subplots(figsize=(6, 6))
        sns.barplot(
            x=data_filter["persentase"],
            y=data_filter.index,
            ax=ax,
            palette="dark",
        )

        # Pengaturan label grafik
        ax.set_xlabel("\nPersentase Keketatan (%)")
        ax.set_ylabel("Kota/Kabupaten\n")

        # Garis bantu vertikal penanda batas kuota penuh (100%)
        ax.axvline(
            100, color="red", linestyle="--", label="Batas Kuota (100%)"
        )
        ax.legend()

        # Render grafik ke dashboard Streamlit
        st.pyplot(fig)

except Exception as e:
    st.error(
        f"Terjadi kesalahan saat memproses data. Pastikan struktur kolom source data sesuai. Error: {e}"
    )