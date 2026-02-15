## Ringkasan Proyek

Dashboard interaktif ini menampilkan analisis penjualan dan segmentasi pelanggan menggunakan dataset Olist (Brazil). Tujuan: menyajikan insight bisnis melalui visualisasi interaktif dan filter untuk eksplorasi data.

## Prasyarat

- Python 3.9+ (direkomendasikan menggunakan virtual environment / conda)
- Git (opsional)
- Paket Python tercantum di `requirements.txt`

## Setup Environment - Anaconda

```bash
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```bash
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Menjalankan Streamlit App

Jalankan salah satu dari file dashboard yang tersedia:

```bash
# Versi utama (root)
streamlit run dashboard_streamlit.py

# Alternatif (di folder dashboard)
python -m streamlit run dashboard/dashboard.py
```

## Fitur Utama

- Filter rentang tanggal transaksi
- Filter kategori produk (multiselect)
- Filter wilayah/state (multiselect)
- Filter segmen pelanggan (RFM)
- KPI cards, tren waktu, peta geografis, top kategori, dan ringkasan statistik

## Struktur Repository

- `Proyek_Analisis_Data.ipynb` — Notebook analisis utama
- `dashboard_streamlit.py` — Dashboard Streamlit (root)
- `dashboard/` — Folder berisi `dashboard.py` dan `main_data.csv`
- `data/` — Dataset Olist (CSV)
- `requirements.txt` — Daftar dependensi
- Dokumentasi lanjutan dan skrip peluncuran

## Data Sumber

Data mentah berasal dari koleksi Olist berikut (lokal di folder `data/`):

- olist_customers_dataset.csv
- olist_geolocation_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_order_reviews_dataset.csv
- olist_orders_dataset.csv
- olist_products_dataset.csv
- olist_sellers_dataset.csv
- product_category_name_translation.csv

Catatan: `dashboard/main_data.csv` adalah agregat pra-komputasi (orders per product_category_name_english) yang dipakai untuk mempercepat dashboard.

## Verifikasi Singkat

Setelah menginstal dependensi, jalankan perintah streamlit di atas dan buka URL yang ditampilkan (biasanya http://localhost:8501).

## Penulis

- Nama: Aflaha Setyaningrum
