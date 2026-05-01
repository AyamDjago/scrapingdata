# Scraping Data Alumni UMM (Apify + LinkedIn)

Script ini melakukan *mass profiling* alumni UMM dari data Excel, lalu mencari kandidat profil LinkedIn berdasarkan **nama** menggunakan actor Apify `harvestapi/linkedin-profile-search-by-name`. Hasil yang terdeteksi sebagai alumni UMM akan disimpan ke file CSV.

## Prasyarat

- Python 3.9+ (disarankan)
- Akun Apify + API Token
- File input Excel bernama `data_input.xlsx` berada di folder yang sama dengan script

## Instalasi

Disarankan memakai virtual environment.

```bash
pip install pandas openpyxl apify-client
```

> `openpyxl` dibutuhkan untuk membaca file `.xlsx` via `pandas`.

## Format File Input (`data_input.xlsx`)

Pastikan file Excel memiliki kolom (header) berikut:

- `Nama Lulusan`
- `NIM`
- `Tahun Masuk`
- `Tanggal Lulus`
- `Fakultas`
- `Program Studi`

Baris lain boleh ada, tapi kolom di atas yang dibaca oleh script.

## Cara Menjalankan

Jalankan script:

```bash
python scraper3.py
```

Lalu isi prompt:

1. **API Token Apify**
2. **Mulai dari baris ke berapa** (1 s/d total baris di Excel)
3. **Berapa banyak data yang diproses** (batch)

Script akan memproses subset data sesuai rentang baris yang kamu pilih.

## Output

- Output berupa CSV dengan nama:

  - `data_$<mulai>_$<akhir>.csv`

- Script hanya menyimpan data jika kandidat profil mengandung kata kunci pendidikan/riwayat yang mengarah ke **"muhammadiyah malang"**.
- Kolom output mencakup data dasar lulusan + informasi LinkedIn (URL, email jika tersedia), lokasi, pekerjaan (present/terakhir), dan beberapa placeholder privasi (IG/TikTok/Facebook/No HP).

## Catatan Penting

- Actor Apify yang dipakai: `harvestapi/linkedin-profile-search-by-name`.
- Kuota/credit Apify bisa habis. Script akan meminta token baru jika terdeteksi error terkait limit/402.
- Scraping LinkedIn dapat dibatasi oleh kebijakan platform. Pastikan penggunaan sesuai aturan, etika, dan regulasi yang berlaku.
