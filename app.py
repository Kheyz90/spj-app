import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime

st.set_page_config(page_title="Aplikasi SPJ v13", layout="wide")
st.title("📋 Sistem Perjalanan Dinas (SPJ) - Versi 13.0")

def clean_currency(value):
    """Mengonversi nilai dari CSV menjadi float dengan aman."""
    if pd.isna(value) or str(value).strip() in ['-', '', '0']:
        return 0.0
    # Karena database Anda sudah tanpa titik, kita cukup ambil angkanya saja
    val_str = str(value).strip().replace(' ', '')
    try:
        return float(val_str)
    except:
        return 0.0

def load_data():
    try:
        # Membaca database biaya (skip 5 baris pertama)
        df_biaya = pd.read_csv('db_biaya.csv', sep=';', skiprows=5)
        df_biaya.columns = df_biaya.columns.str.strip()
        # Membaca database wilayah
        df_kota = pd.read_csv('db_wilayah.csv', sep=';', header=None)
        df_kota.columns = ['WILAYAH', 'KOTA']
        return df_biaya, df_kota
    except Exception as e:
        st.error(f"Gagal memuat database: {e}")
        return None, None

df_biaya, df_kota = load_data()

if df_biaya is not None:
    st.subheader("1. Data Personel & Penugasan")
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama yang Ditugaskan")
        jabatan = st.selectbox("Jabatan", df_biaya['Jabatan'].dropna().unique())
        perihal = st.text_area("Perihal Penugasan", help="Teks akan otomatis memanjang di PDF")
    with col2:
        pemberi_tugas = st.text_input("Nama Pejabat Menugaskan", value="Destina Paningrum, S.E., M.M")
        tgl = st.date_input("Tanggal Berangkat")
        durasi = st.number_input("Durasi (Hari)", min_value=1, step=1)

    st.subheader("2. Lokasi & Transportasi")
    cl1, cl2, cl3 = st.columns(3)
    with cl1:
        list_wilayah = df_biaya['WILAYAH'].dropna().unique()
        wilayah = st.selectbox("Wilayah Tujuan", list_wilayah)
    with cl2:
        kota_pilihan = df_kota[df_kota['WILAYAH'] == wilayah]['KOTA'].unique()
        tujuan = st.selectbox("Kota Spesifik", kota_pilihan)
    with cl3:
        transport_alat = st.text_input("Alat Transportasi", value="Mobil Dinas")

    st.divider()
    st.subheader("3. Rincian Biaya")
    cm_col, co_col = st.columns(2)
    with cm_col:
        st.write("**Frekuensi Makan:**")
        f1, f2, f3 = st.columns(3)
        with f1: q_pagi = st.number_input("Pagi (X)", min_value=0, value=int(durasi))
        with f2: q_siang = st.number_input("Siang (X)", min_value=0, value=int(durasi))
        with f3: q_malam = st.number_input("Malam (X)", min_value=0, value=int(durasi))
    with co_col:
        st.write("**Opsi Biaya (Database):**")
        op1, op2, op3 = st.columns(3)
        with op1: opt_bbm = st.checkbox("BBM")
        with op2: opt_akom = st.checkbox("Akomodasi")
        with op3: opt_taxi = st.checkbox("Taxi")

    extra_costs = []
    st.write("**Biaya Tambahan Manual:**")
    ex_cols = st.columns(2)
    for i in range(4):
        with ex_cols[i % 2]:
            cx1, cx2 = st.columns([2, 1])
            with cx1: k = st.text_input(f"Keterangan {i+1}", key=f"exk_{i}")
            with cx2: n = st.number_input(f"Nominal {i+1}", min_value=0, key=f"exn_{i}")
            if k and n > 0: extra_costs.append({'k': k, 'n': n})

    if st.button("Generate SPJ Profesional"):
        row = df_biaya[(df_biaya['Jabatan'] == jabatan) & (df_biaya['WILAYAH'] == wilayah)]
        if not row.empty:
            # Pengambilan data murni dari database
            tot_pagi = clean_currency(row.iloc[0]['Uang Makan']) * q_pagi
            tot_siang = clean_currency(row.iloc[0]['Makan Siang']) * q_siang
            tot_malam = clean_currency(row.iloc[0]['Makan Malam']) * q_malam
            tot_saku = clean_currency(row.iloc[0]['Uang Saku']) * durasi
            
            v_bbm = clean_currency(row.iloc[0]['BBM']) if opt_bbm else 0
            v_akom = clean_currency(row.iloc[0]['Biaya Akomodasi']) if opt_akom else 0
            v_taxi = clean_currency(row.iloc[0]['Taxi']) if opt_taxi else 0
            
            total_akhir = tot_pagi + tot_siang + tot_malam + tot_saku + v_bbm + v_akom + v_taxi + sum(x['n'] for x in extra_costs)
            tgl_str = tgl.strftime("%d/%m/%Y")

            # --- PDF ---
            pdf = FPDF()
            pdf.add_page()
            try: pdf.image("logo_uss-removebg-preview.png", 10, 8, 33)
            except: pass

            pdf.ln(25)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(190, 10, "SURAT PERJALANAN DINAS", ln=True, align='C')
            pdf.ln(5)

            pdf.set_font("Arial", size=9)
            pdf.cell(40, 6, "Unit", 0); pdf.cell(150, 6, ": Universitas Sahid Surakarta", 0, 1)
            pdf.cell(40, 6, "Nama ditugaskan", 0); pdf.cell(150, 6, f": {nama}", 0, 1)
            pdf.cell(40, 6, "Jabatan", 0); pdf.cell(150, 6, f": {jabatan}", 0, 1)
            
            # Perihal Memanjang Sejajar
            pdf.cell(40, 6, "Perihal Penugasan", 0)
            pdf.set_x(50) 
            pdf.multi_cell(150, 6, f": {perihal}", align='L')
            
            # Transportasi & TTD Sejajar
            y_sekarang = pdf.get_y() + 2
            pdf.set_y(y_sekarang)
            pdf.cell(40, 6, "Transportasi", 0); pdf.cell(60, 6, f": {transport_alat}", 0, 0)
            
            # TTD di kanan Transportasi
            pdf.set_x(115)
            pdf.cell(75, 6, "TTD yang menugaskan,", 0, 1, 'C')
            
            # Baris Berikutnya
            pdf.cell(40, 6, "Waktu Penugasan", 0); pdf.cell(60, 6, f": {int(durasi)} hari ({tgl_str})", 0, 1)
            pdf.cell(40, 6, "Tujuan", 0); pdf.cell(60, 6, f": {tujuan} ({wilayah})", 0, 1)

            # Nama Terang Penugas (sejajar vertikal ke bawah)
            pdf.set_xy(115, y_sekarang + 18)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(75, 6, f"( {pemberi_tugas} )", 0, 1, 'C')

            pdf.ln(8)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(95, 7, "Komponen Biaya", 1, 0, 'C')
            pdf.cell(35, 7, "Satuan", 1, 0, 'C')
            pdf.cell(60, 7, "Jumlah (Rp)", 1, 1, 'C')

            pdf.set_font("Arial", size=9)
            def fmt(x): return f"{x:,.0f}".replace(',', '.')

            if tot_pagi > 0: pdf.cell(95, 7, "Uang Makan Pagi", 1); pdf.cell(35, 7, f"{int(q_pagi)}x", 1, 0, 'C'); pdf.cell(60, 7, fmt(tot_pagi), 1, 1, 'R')
            if tot_siang > 0: pdf.cell(95, 7, "Uang Makan Siang", 1); pdf.cell(35, 7, f"{int(q_siang)}x", 1, 0, 'C'); pdf.cell(60, 7, fmt(tot_siang), 1, 1, 'R')
            if tot_malam > 0: pdf.cell(95, 7, "Uang Makan Malam", 1); pdf.cell(35, 7, f"{int(q_malam)}x", 1, 0, 'C'); pdf.cell(60, 7, fmt(tot_malam), 1, 1, 'R')
            pdf.cell(95, 7, "Uang Saku", 1); pdf.cell(35, 7, f"{int(durasi)} hari", 1, 0, 'C'); pdf.cell(60, 7, fmt(tot_saku), 1, 1, 'R')
            
            if opt_bbm: pdf.cell(95, 7, "BBM", 1); pdf.cell(35, 7, "-", 1, 0, 'C'); pdf.cell(60, 7, fmt(v_bbm), 1, 1, 'R')
            if opt_akom: pdf.cell(95, 7, "Biaya Akomodasi", 1); pdf.cell(35, 7, "-", 1, 0, 'C'); pdf.cell(60, 7, fmt(v_akom), 1, 1, 'R')
            if opt_taxi: pdf.cell(95, 7, "Taxi", 1); pdf.cell(35, 7, "-", 1, 0, 'C'); pdf.cell(60, 7, fmt(v_taxi), 1, 1, 'R')
            
            for item in extra_costs:
                pdf.cell(95, 7, item['k'], 1); pdf.cell(35, 7, "-", 1, 0, 'C'); pdf.cell(60, 7, fmt(item['n']), 1, 1, 'R')

            pdf.set_font("Arial", 'B', 9)
            pdf.cell(130, 7, "TOTAL ESTIMASI BIAYA ", 1, 0, 'R'); pdf.cell(60, 7, fmt(total_akhir), 1, 1, 'R')

            # Footer TTD
            pdf.ln(12)
            pdf.set_font("Arial", size=8)
            cw = 190 / 4
            pdf.cell(cw, 5, "Yang Membuat,", 0, 0, 'C')
            pdf.cell(cw, 5, "Yang Membayarkan,", 0, 0, 'C')
            pdf.cell(cw, 5, "Penerima Dana,", 0, 0, 'C')
            pdf.cell(cw, 5, "Menyetujui,", 0, 1, 'C')
            pdf.ln(15)
            pdf.cell(cw, 5, "( ............................ )", 0, 0, 'C')
            pdf.cell(cw, 5, "( ............................ )", 0, 0, 'C')
            pdf.set_font("Arial", 'B', 8); pdf.cell(cw, 5, f"( {nama} )", 0, 0, 'C')
            pdf.set_font("Arial", size=8); pdf.cell(cw, 5, "( ............................ )", 0, 1, 'C')

            pdf_out = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_out).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="SPJ_{nama}.pdf"><button style="background-color:#075985;color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;">📥 DOWNLOAD PDF FINAL v13</button></a>', unsafe_allow_html=True)