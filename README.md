<div align="center">

  # 🧮 Kalkulator Metode Regula Falsi
  **Aplikasi Interaktif Pencarian Akar Persamaan Non-Linier Berbasis Streamlit**

  [![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
  [![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
  [![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
  [![Altair](https://img.shields.io/badge/Altair-5.0%2B-4682B4?style=for-the-badge)](https://altair-viz.github.io/)

  ---

  <p align="center">
    Proyek Tugas Komputasi Numerik (UTS) — Kelompok 4
  </p>

</div>

## 📌 Gambaran Umum

Aplikasi GUI interaktif ini dibangun menggunakan **Streamlit** untuk mempermudah perhitungan dan visualisasi pencarian akar persamaan non-linier $f(x) = 0$ menggunakan **Metode Regula Falsi** (Posisi Palsu). 

Aplikasi ini dirancang fleksibel sehingga pengguna dapat memasukkan fungsi matematika bebas, memilih selang awal $[a, b]$, serta mengatur toleransi error $\epsilon$ dan maksimum iterasi $N$.

---

## ✨ Fitur Utama

- 🧠 **Parsing Fungsi Dinamis & Aman:** Mendukung penulisan fungsi matematika bebas (seperti `x^3 - 4x + 2`, `cos(x) - x`, `exp(-x) - x`) tanpa `eval()` mentah.
- 📊 **Tabel Iterasi Komprehensif:** Menyajikan nilai $a$, $b$, $f(a)$, $f(b)$, $x_r$, $f(x_r)$, hingga nilai mutlak galat $|f(x_r)|$ secara sistematis.
- 📈 **Visualisasi Interaktif:**
  - **Grafik Kurva & Garis Sekan:** Menampilkan pergerakan titik $x_r$ dan garis potong antar-iterasi.
  - **Grafik Konvergensi:** Laju penurunan error $|f(x_r)|$ dalam skala logaritma terhadap batas toleransi.
- ⚡ **Auto-Bootstrap Dependency:** Skrip otomatis membuat *virtual environment* (`.venv`) dan memasang dependensi jika belum ada di sistem pengguna.

---

## 🛠️ Teknologi yang Digunakan

| Komponen | Teknologi |
| :--- | :--- |
| **Bahasa Pemrograman** | Python 3.10+ |
| **Framework GUI** | Streamlit |
| **Komputasi & Data** | NumPy, Pandas |
| **Visualisasi Grafik** | Altair |
| **Parser Ekspresi** | Python AST (*Abstract Syntax Tree*) |

---

## 📐 Algoritma Regula Falsi

Metode Regula Falsi memanfaatkan garis lurus (sekan) yang menghubungkan titik $(a, f(a))$ dan $(b, f(b))$. Titik potong garis tersebut dengan sumbu-$x$ ditentukan oleh rumus:

$$x_r = \frac{f(a) \cdot b - f(b) \cdot a}{f(a) - f(b)}$$

### Langkah Pembaruan Selang:
1. Hitung $f(x_r)$.
2. Jika $|f(x_r)| \le \epsilon$, maka $x_r$ adalah akar yang dicari (kriteria berhenti).
3. Jika $f(x_r) \cdot f(b) < 0$, perbarui $a = x_r$.
4. Jika tidak, perbarui $b = x_r$.

---

## 🚀 Cara Menjalankan Project

### 1. Clone Repositori
```bash
git clone [https://github.com/zackyirfan/Kelompok-4-UTS-Komnum.git](https://github.com/zackyirfan/Kelompok-4-UTS-Komnum.git)
cd Kelompok-4-UTS-Komnum