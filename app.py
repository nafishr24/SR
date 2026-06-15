import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Konfigurasi halaman utama Streamlit (Harus di paling atas)
st.set_page_config(
    page_title="Data Pelamar TIK", page_icon="📊", layout="wide"
)

# 1. Judul Aplikasi dengan Gaya Markdown + Subtitle
st.markdown(
    "<h1 style='text-align: center; color: #1E3A8A;'>📊 Data Pelamar TIK Sekolah Rakyat</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #6B7280; font-size: 1.2rem;'>Dashboard Pemantauan Formasi dan Keketatan Pelamar Berdasarkan Wilayah</p>",
    unsafe_allow_html=True,
)
st.write("---")


# Fungsi rekap (tetap sama)
def rekap(df: pd.DataFrame) -> pd.DataFrame:
    df[["provinsi", "kota", "formasi"]] = (
        df["Wilayah Yang Dipilih"].str.strip()
    ).str.split(" - ", expand=True)
    df = df.drop(columns=["Wilayah Yang Dipilih", "Timestamp"])

    df["provinsi"] = df["provinsi"].str.replace(
        r"[^a-zA-Z]+", "", regex=True
    )
    df["formasi"] = (
        df["formasi"].str.replace(r"\D+", "", regex=True).astype(int)
    )

    rekap_df = df.groupby(["provinsi", "kota"]).agg(
        pelamar=("kota", "count"), formasi=("formasi", "first")
    )
    rekap_df["persentase"] = (
        rekap_df["pelamar"] / rekap_df["formasi"] * 100
    ).round(2)
    return rekap_df


@st.cache_data
def load_data():
    link_sheet = "https://docs.google.com/spreadsheets/d/1VX1Rk_WjyGVx3AiOlsocMRB5xRT0R8T85RP6c4j7Xh0/export?format=csv&gdid=0"
    df_raw = pd.read_csv(link_sheet)
    return rekap(df_raw)


try:
    cek = load_data()
    list_provinsi = cek.index.get_level_values("provinsi").unique()

    # Sidebar untuk Filter agar halaman utama lebih bersih
    st.sidebar.header("⚙️ Filter Wilayah")
    pilihan_provinsi = st.sidebar.selectbox(
        "Pilih Provinsi:", list_provinsi
    )

    # Filter data sesuai provinsi pilihan
    data_filter = cek.xs(pilihan_provinsi, level="provinsi")

    # ---- BAGIAN RINGKASAN DATA (METRICS) ----
    st.subheader(f"📍 Ringkasan - Provinsi {pilihan_provinsi}")

    # Hitung total untuk metric
    total_kota = len(data_filter)
    total_pelamar = data_filter["pelamar"].sum()
    total_formasi = data_filter["formasi"].sum()
    rata_persentase = (total_pelamar / total_formasi * 100).round(2)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Kota/Kab", value=f"{total_kota} Wilayah")
    with col2:
        st.metric(label="Total Pelamar", value=f"{total_pelamar} Orang")
    with col3:
        st.metric(label="Total Formasi", value=f"{total_formasi} Slot")
    with col4:
        st.metric(
            label="Rata-rata Keketatan",
            value=f"{rata_persentase}%",
            delta="Overcapacity" if rata_persentase > 100 else "Normal",
        )

    st.write("---")

    # ---- BAGIAN TABEL DATA & GRAFIK (LAYOUT KOLOM) ----
    col_tabel, col_grafik = st.columns([1, 1])

    with col_tabel:
        st.subheader("📋 Tabel Detail Wilayah")
        # Menampilkan dataframe dengan style interaktif (bisa di-sort)
        st.dataframe(
            data_filter.style.background_gradient(
                cmap="Blues", subset=["persentase"]
            ),
            use_container_width=True,
            height=350,
        )

    with col_grafik:
        st.subheader("📊 Grafik Keketatan (%) per Kota")

        # Membuat grafik batang menggunakan Matplotlib/Seaborn
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(
            x=data_filter["persentase"],
            y=data_filter.index,
            ax=ax,
            palette="Blues_r",
        )
        ax.set_xlabel("Persentase Keketatan (%)")
        ax.set_ylabel("Kota/Kabupaten")
        ax.axvline(
            100, color="red", linestyle="--", label="Batas Kuota (100%)"
        )
        ax.legend()

        # Menampilkan grafik ke Streamlit
        st.pyplot(fig)

except Exception as e:
    st.error(f"Terjadi kesalahan teknis: {e}")