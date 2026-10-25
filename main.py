"""
Author: Kelompok 4
Title: Kalkulator Metode Regula Falsi (fungsi bebas + grafik)

ALGORITMA UTAMA REGULA FALSI:
1. Menentukan selang awal [a, b] di mana f(a) * f(b) < 0.
2. Menghitung nilai titik potong (xr) menggunakan rumus:
      xr = (f(a)*b - f(b)*a) / (f(a) - f(b))
3. Menghitung evaluasi nilai f(xr).
4. Mengecek kondisi toleransi |f(xr)| <= e (apakah akar sudah ditemukan).
5. Memperbarui batas selang:
   - Jika f(xr) * f(b) < 0, maka batas 'a' diperbarui menjadi xr.
   - Jika tidak, maka batas 'b' diperbarui menjadi xr.
6. Ulangi hingga iterasi maksimal N atau hingga toleransi terpenuhi.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

# List dependensi library Python yang dibutuhkan aplikasi
DEPENDENSI = {
    "streamlit": "streamlit>=1.30",
    "pandas": "pandas>=2.0",
    "numpy": "numpy>=1.24",
    "altair": "altair>=5.0",
}


def _bootstrap():
    """Fungsi pembantu: Mengecek & memasang library Python secara otomatis jika belum ada."""
    berkas = Path(__file__).resolve()
    py = sys.executable

    if any(importlib.util.find_spec(modul) is None for modul in DEPENDENSI):
        venv = berkas.parent / ".venv"
        py_venv = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        try:
            if not py_venv.exists():
                print("Membuat lingkungan virtual (.venv)...")
                subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
                print("Memasang dependensi (pertama kali bisa beberapa menit)...")
                subprocess.check_call([str(py_venv), "-m", "pip", "install", "-q", *DEPENDENSI.values()])
        except (subprocess.CalledProcessError, OSError) as err:
            print(f"\nGagal memasang dependensi: {err}")
            print("Pastikan komputer terhubung ke internet lalu coba lagi.")
            sys.exit(1)
        py = str(py_venv)

    print("Menjalankan aplikasi... (tekan Ctrl+C untuk berhenti)")
    proses = subprocess.Popen([py, "-m", "streamlit", "run", str(berkas)], stdin=subprocess.PIPE, text=True)
    try:
        proses.stdin.write("\n")
        proses.stdin.close()
    except OSError:
        pass
    try:
        proses.wait()
    except KeyboardInterrupt:
        proses.terminate()
    sys.exit(proses.returncode or 0)


# Jalankan bootstrap installer jika file dipanggil langsung lewat terminal 'python filename.py'
if __name__ == "__main__" and "streamlit" not in sys.modules:
    _bootstrap()

import ast
import math
import operator
import re

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Pengaturan judul tab browser aplikasi
st.set_page_config(
    page_title="Kalkulator Regula Falsi",
    page_icon="🧮",
    layout="wide",
)

# ---------------------------------------------------------------------------
# PARSER FUNGSI: Mengubah teks input f(x) dari user menjadi fungsi matematika Python
# ---------------------------------------------------------------------------

# Daftar fungsi & operator matematika yang diizinkan untuk dievaluasi
FUNGSI_AMAN = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "asin": np.arcsin,
    "acos": np.arccos,
    "atan": np.arctan,
    "sinh": np.sinh,
    "cosh": np.cosh,
    "tanh": np.tanh,
    "exp": np.exp,
    "log": np.log,  # Logaritma natural (ln)
    "ln": np.log,
    "log10": np.log10,
    "log2": np.log2,
    "sqrt": np.sqrt,
    "cbrt": np.cbrt,
    "abs": np.abs,
}
KONSTANTA = {"pi": np.pi, "e": np.e}
OPERATOR_BINER = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: np.power,
}
OPERATOR_UNER = {ast.UAdd: operator.pos, ast.USub: operator.neg}

# Regex untuk menangani perkalian implisit (contoh: '4x' diubah menjadi '4*x')
POLA_KALI = re.compile(r"(?<=[\dx)])\s*(?=(?:x(?![a-z])|\(|pi(?![a-z])|[a-z]{2,}\d*\())")


def _hitung(node, x):
    """Mengevaluasi struktur pohon matematika (AST Node) secara rekursif berdasarkan nilai x."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return np.float64(node.value)
        raise ValueError("Hanya angka yang boleh dipakai sebagai konstanta.")
    if isinstance(node, ast.Name):
        if node.id == "x":
            return x
        if node.id in KONSTANTA:
            return np.float64(KONSTANTA[node.id])
        raise ValueError(f"Nama '{node.id}' tidak dikenali. Gunakan x sebagai variabel.")
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATOR_BINER:
        return OPERATOR_BINER[type(node.op)](_hitung(node.left, x), _hitung(node.right, x))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATOR_UNER:
        return OPERATOR_UNER[type(node.op)](_hitung(node.operand, x))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        nama = node.func.id
        if nama not in FUNGSI_AMAN:
            raise ValueError(f"Fungsi '{nama}' tidak didukung.")
        if len(node.args) != 1 or node.keywords:
            raise ValueError(f"Fungsi '{nama}' harus punya tepat satu argumen.")
        return FUNGSI_AMAN[nama](_hitung(node.args[0], x))
    raise ValueError("Ekspresi mengandung bentuk yang tidak didukung.")


def buat_fungsi(teks):
    """
    FUNGSI PEMROSES INPUT:
    Mengubah teks input pengguna (seperti 'x^3 - 4x + 2') menjadi fungsi f(x)
    yang siap dihitung nilainya oleh algoritma Regula Falsi.
    """
    ekspresi = teks.strip().lower()
    ekspresi = re.sub(r"^f\s*\(\s*x\s*\)\s*=\s*", "", ekspresi)  # Hapus awalan "f(x) =" jika ketikan user menyertakannya
    if not ekspresi:
        raise ValueError("Fungsi tidak boleh kosong.")
    if len(ekspresi) > 200:
        raise ValueError("Fungsi terlalu panjang (maksimal 200 karakter).")

    # Konversi format penulisan umum ke format standar Python ('^' -> '**', ',' -> '.')
    ekspresi = ekspresi.replace("^", "**").replace(",", ".")
    ekspresi = POLA_KALI.sub("*", ekspresi)

    try:
        pohon = ast.parse(ekspresi, mode="eval")
    except SyntaxError:
        raise ValueError("Penulisan fungsi tidak valid. Contoh: x**3 - 4*x + 2") from None

    # Uji coba validasi dengan memasukkan nilai x = 1.0
    with np.errstate(all="ignore"):
        _hitung(pohon.body, np.float64(1.0))

    def f(x):
        with np.errstate(all="ignore"):
            return _hitung(pohon.body, np.asarray(x, dtype=float))

    return f


# ---------------------------------------------------------------------------
# INTI ALGORITMA METODE REGULA FALSI
# ---------------------------------------------------------------------------


def regula_falsi(f, a, b, tol, n):
    """
    EKSEKUSI ALGORITMA REGULA FALSI:
    Input  : f   -> Fungsi f(x)
             a   -> Batas atas selang awal
             b   -> Batas bawah selang awal
             tol -> Toleransi error (|f(xr)| <= tol)
             n   -> Maksimum iterasi

    Output : (baris, iterasi_solusi, akar_solusi, pesan_error)
    """
    baris = []
    iterasi_solusi = None
    akar_solusi = None
    pesan_error = None

    # Pengulangan iterasi dari i = 1 sampai i = n
    for i in range(1, n + 1):
        # 1. Hitung nilai fungsi pada titik ujung selang saat ini: f(a) dan f(b)
        fa = float(f(a))
        fb = float(f(b))

        # Cek Validasi Domain: Pastikan hasil f(a) dan f(b) berupa angka terdefinisi (bukan tak hingga / NaN)
        if not (math.isfinite(fa) and math.isfinite(fb)):
            pesan_error = (
                f"Iterasi {i} berhenti: f(a) atau f(b) tidak terdefinisi. Periksa domain fungsi."
            )
            break

        # Cek Pembagian Nol: Jika f(a) == f(b), rumus xr akan membagi angka dengan 0 (garis sejajar)
        if fa == fb:
            pesan_error = (
                f"Iterasi {i} berhenti: f(a) sama dengan f(b), pembagian dengan nol pada perhitungan xr."
            )
            break

        # 2. RUMUS UTAMA REGULA FALSI (Menghitung titik potong garis sekan xr)
        # Formula: xr = (f(a)*b - f(b)*a) / (f(a) - f(b))
        xr = ((fa * b) - (fb * a)) / (fa - fb)
        
        # 3. Hitung evaluasi nilai fungsi pada titik baru: f(xr)
        fxr = float(f(xr))

        # Cek Validasi Domain pada nilai xr baru
        if not math.isfinite(fxr):
            pesan_error = f"Iterasi {i} berhenti: f(xr) tidak terdefinisi untuk xr = {xr:.5f}."
            break

        # Hitung f(xr) * f(b) untuk penentuan pembaharuan selang pada iterasi berikutnya
        fxr_fb = fxr * fb
        abs_fxr = abs(fxr)  # Nilai mutlak f(xr) digunakan sebagai acuan Galat / Error

        # Simpan data iterasi i ke dalam tabel hasil
        baris.append([i, a, b, fa, fb, xr, fxr, fxr_fb, abs_fxr])

        # 4. CEK KRITERIA BERHENTI (Toleransi Error Tercapai)
        # Jika nilai |f(xr)| sudah lebih kecil atau sama dengan toleransi error (tol), akar ditemukan!
        if iterasi_solusi is None and abs_fxr <= tol:
            iterasi_solusi = i
            akar_solusi = xr

        # 5. ATURAN PEMBARUAN SELANG (REPLACEMENT RULE)
        # Jika f(xr) * f(b) < 0, berarti tanda berubah antara xr dan b -> akar ada di [xr, b], ganti a = xr
        if fxr_fb < 0:
            a = xr
        # Jika f(xr) * f(b) >= 0, berarti akar berada di selang [a, xr], ganti b = xr
        else:
            b = xr

    return baris, iterasi_solusi, akar_solusi, pesan_error


# ---------------------------------------------------------------------------
# FUNGSI PEMBUATAN GRAFIK (Untuk Visualisasi Visual)
# ---------------------------------------------------------------------------


def grafik_fungsi(f, df, a0, b0, akar):
    """Membuat grafik kurva f(x), garis sekan/potong tiap iterasi, dan titik lokasi akar."""
    titik_x = [a0, b0] + df["xr"].tolist()
    batas_kiri, batas_kanan = min(titik_x), max(titik_x)
    pad = (batas_kanan - batas_kiri) * 0.3 or 1.0
    domain_x = [batas_kiri - pad, batas_kanan + pad]

    xs = np.linspace(domain_x[0], domain_x[1], 500)
    ys = np.broadcast_to(np.asarray(f(xs), dtype=float), xs.shape).copy()
    ys[~np.isfinite(ys)] = np.nan

    nilai = np.concatenate([ys[np.isfinite(ys)], df["f(xr)"].to_numpy(), [0.0]])
    y_bawah, y_atas = np.percentile(nilai, [1, 99])
    y_bawah, y_atas = min(y_bawah, 0.0), max(y_atas, 0.0)
    pad_y = (y_atas - y_bawah) * 0.1 or 1.0
    domain_y = [y_bawah - pad_y, y_atas + pad_y]

    skala_x = alt.Scale(domain=domain_x, clamp=True)
    skala_y = alt.Scale(domain=domain_y, clamp=True)

    def X(kolom):
        return alt.X(f"{kolom}:Q", scale=skala_x, title="x")

    def Y(kolom):
        return alt.Y(f"{kolom}:Q", scale=skala_y, title="f(x)")

    kurva = pd.DataFrame({"x": xs, "fx": ys})
    lapisan = [
        # Kurva grafik f(x) garis biru
        alt.Chart(kurva).mark_line(color="#2563eb", strokeWidth=2).encode(x=X("x"), y=Y("fx")),
        # Garis acuan y=0 (Sumbu X)
        alt.Chart(pd.DataFrame({"y": [0.0]}))
        .mark_rule(color="gray", strokeDash=[4, 4])
        .encode(y=Y("y")),
        # Garis batas awal a dan b (garis oranye putus-putus)
        alt.Chart(pd.DataFrame({"x": [a0, b0], "label": ["a awal", "b awal"]}))
        .mark_rule(color="#f59e0b", strokeDash=[2, 2])
        .encode(x=X("x"), tooltip=["label:N", alt.Tooltip("x:Q", format=".5f")]),
    ]

    # Garis sekan/potong untuk 5 iterasi awal
    garis = df.head(5).rename(columns={"Iterasi": "iterasi", "f(a)": "fa", "f(b)": "fb"})
    lapisan.append(
        alt.Chart(garis)
        .mark_rule(color="#f59e0b", opacity=0.6)
        .encode(
            x=X("a"),
            y=Y("fa"),
            x2="b:Q",
            y2="fb:Q",
            tooltip=["iterasi:Q"],
        )
    )

    # Titik merah pembentukan xr pada tiap iterasi
    titik = pd.DataFrame({"iterasi": df["Iterasi"], "xr": df["xr"], "fxr": df["f(xr)"]})
    tip = ["iterasi:Q", alt.Tooltip("xr:Q", format=".5f"), alt.Tooltip("fxr:Q", format=".5f")]
    titik_chart = alt.Chart(titik)
    lapisan.append(
        titik_chart.mark_point(filled=True, color="#ef4444", size=60).encode(x=X("xr"), y=Y("fxr"), tooltip=tip)
    )
    lapisan.append(
        alt.Chart(titik.head(10))
        .mark_text(dy=-12, color="#ef4444")
        .encode(x=X("xr"), y=Y("fxr"), text="iterasi:Q")
    )

    # Penanda berlian hijau pada titik posisi akar hasil akhir
    if akar is not None:
        data_akar = pd.DataFrame({"x": [akar], "y": [float(f(akar))]})
        lapisan.append(
            alt.Chart(data_akar)
            .mark_point(shape="diamond", filled=True, color="#10b981", size=220)
            .encode(x=X("x"), y=Y("y"), tooltip=[alt.Tooltip("x:Q", title="akar", format=".5f")])
        )

    return alt.layer(*lapisan).properties(height=420, width="container").interactive()


def grafik_konvergensi(df, tol):
    """Membuat grafik laju penurunan error |f(xr)| terhadap penambahan iterasi."""
    skala_log = alt.Scale(type="log")
    data = pd.DataFrame(
        {
            "iterasi": df["Iterasi"],
            "xr": df["xr"],
            "galat": df["|f(xr)|"].clip(lower=1e-16),
        }
    )
    lapisan = [
        alt.Chart(data)
        .mark_line(point=True, color="#2563eb")
        .encode(
            x=alt.X("iterasi:Q", title="Iterasi", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("galat:Q", title="|f(xr)| (skala log)", scale=skala_log),
            tooltip=["iterasi:Q", alt.Tooltip("xr:Q", format=".5f"), alt.Tooltip("galat:Q", format=".3e")],
        )
    ]
    if tol > 0:
        lapisan.append(
            alt.Chart(pd.DataFrame({"toleransi": [tol]}))
            .mark_rule(color="#ef4444", strokeDash=[4, 4])
            .encode(y=alt.Y("toleransi:Q", scale=skala_log))
        )
    return alt.layer(*lapisan).properties(height=360, width="container")


# ---------------------------------------------------------------------------
# ANTARMUKA TAMPILAN (STREAMLIT GUI)
# ---------------------------------------------------------------------------

HEADERS = ["Iterasi", "a", "b", "f(a)", "f(b)", "xr", "f(xr)", "f(xr).f(b)", "|f(xr)|"]

BANTUAN_FUNGSI = (
    "Variabel: x. Operator: + - * / dan ** (atau ^) untuk pangkat. "
    "Fungsi: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, exp, log, ln, sqrt, abs. "
    "Contoh: x**3 - 4*x + 2, cos(x) - x, exp(-x) - x."
)

st.title("Kalkulator Regula Falsi")
st.caption("Masukkan fungsi f(x) apa saja, atur interval dan toleransi, lalu lihat tabel iterasi dan grafiknya.")

# Form Input Parameter Matematika dari Pengguna
with st.form("form_regula_falsi"):
    teks_fungsi = st.text_input(
        "f(x) =",
        value="x**3 - 4*x + 2",
        placeholder="contoh: x**3 - 4*x + 2",
        help=BANTUAN_FUNGSI,
    )
    k1, k2, k3, k4 = st.columns(4)
    a = k1.number_input("a (batas atas)", value=1.0, step=0.1, format="%.5f")
    b = k2.number_input("b (batas bawah)", value=0.0, step=0.1, format="%.5f")
    tol = k3.number_input(
        "e (toleransi error)",
        value=0.001,
        min_value=0.0,
        step=0.0001,
        format="%.6f",
    )
    n = k4.number_input("N (iterasi maksimal)", value=10, min_value=1, max_value=1000, step=1)

    enter = st.form_submit_button("Enter", type="primary", use_container_width=True)

# PROSES EKSEKUSI SAAT TOMBOL ENTER DITEKAN
if enter:
    n = int(n)

    # 1. Parsing teks input ke bentuk fungsi matematika
    try:
        f = buat_fungsi(teks_fungsi)
    except ValueError as err:
        st.error(f"Fungsi tidak valid: {err}")
        st.stop()

    st.markdown(f"Fungsi yang dipakai: `f(x) = {teks_fungsi.strip()}`")

    # 2. Peringatan syarat awal Regula Falsi: f(a) dan f(b) sebaiknya berlawanan tanda
    if f(a) * f(b) > 0:
        st.warning("f(a) dan f(b) bertanda sama. Akar mungkin tidak berada di antara a dan b.")

    # 3. Panggil fungsi algoritma regula_falsi
    baris, iterasi_solusi, akar_solusi, pesan_error = regula_falsi(f, a, b, tol, n)

    if pesan_error:
        st.error(pesan_error)

    # 4. Tampilkan Hasil Perhitungan Akar & Tabel Iterasi
    if baris:
        if iterasi_solusi:
            st.success(
                f"Solusi pertama kali ditemukan pada iterasi ke-{iterasi_solusi} "
                f"dengan nilai xr ≈ {akar_solusi:.5f}"
            )
            m1, m2, m3 = st.columns(3)
            m1.metric("Iterasi solusi", iterasi_solusi)
            m2.metric("Akar (xr)", f"{akar_solusi:.5f}")
            m3.metric("|f(xr)|", f"{abs(float(f(akar_solusi))):.5f}")
        else:
            st.info(f"Hingga iterasi ke-{n}, toleransi error belum tercapai.")

        df = pd.DataFrame(baris, columns=HEADERS)

        # Mewarnai baris tabel tempat solusi ditemukan
        def sorot(row):
            gaya = "background-color: #d1fae5; color: #065f46" if row["Iterasi"] == iterasi_solusi else ""
            return [gaya] * len(row)

        format_kolom = {kolom: "{:.5f}" for kolom in HEADERS if kolom != "Iterasi"}
        tabel = df.style.apply(sorot, axis=1).format(format_kolom)

        st.subheader("Tabel iterasi")
        st.dataframe(tabel, hide_index=True)

        # 5. Tampilkan Visualisasi Grafik
        st.subheader("Grafik")
        tab1, tab2 = st.tabs(["Fungsi dan iterasi", "Konvergensi |f(xr)|"])
        with tab1:
            st.altair_chart(grafik_fungsi(f, df, a, b, akar_solusi))
            st.caption(
                "Garis biru: f(x). Titik merah: xr tiap iterasi. "
                "Berlian hijau: posisi akar ditemukannya titik potong."
            )
        with tab2:
            st.altair_chart(grafik_konvergensi(df, tol))
            st.caption("Garis merah putus-putus menunjukkan toleransi error e.")
else:
    st.info("Isi fungsi, nilai a, b, e, dan N, lalu tekan Enter.")