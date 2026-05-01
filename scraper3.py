import pandas as pd
import time
import os
from apify_client import ApifyClient

# --- 1. KONFIGURASI ---
APIFY_API_TOKEN = 'isi dengan api apify' 
client = ApifyClient(APIFY_API_TOKEN)
FILE_INPUT = 'data_input.xlsx' 

def pisahkan_nama(nama_lengkap):
    if pd.isna(nama_lengkap) or str(nama_lengkap).strip() == "" or str(nama_lengkap).lower() == "nan":
        return "", ""
        
    kata = str(nama_lengkap).strip().split()
    if len(kata) == 0: return "", ""
    elif len(kata) == 1: return kata[0], ""
    elif len(kata) == 2: return kata[0], kata[1]
    else:
        first_name = " ".join(kata[:2])
        last_name = " ".join(kata[2:])
        return first_name, last_name

def klasifikasi_status(headline, company, occupation):
    teks_gabungan = f"{headline} {company} {occupation}".lower()
    
    if any(key in teks_gabungan for key in ['intern', 'magang', 'asisten', 'student', 'mahasiswa']):
        return "Mahasiswa / Magang"
    
    bumn_keywords = ['bumn', 'telkom', 'pertamina', 'pln', 'pt kai', 'pelindo', 'angkasa pura', 'mandiri', 'bri', 'bni', 'btn', 'pegadaian']
    pns_keywords = ['kementerian', 'dinas', 'pemerintah', 'pemkot', 'pemkab', 'pemprov', 'badan pusat', 'asn', 'cpns', 'puskesmas', 'rsud', 'kpu', 'bawaslu', 'polri', 'tni', 'kejaksaan']
    pendidikan_keywords = ['guru', 'dosen', 'teacher', 'lecturer', 'sekolah', 'universitas', 'institute', 'politeknik', 'yayasan pendidikan']
    wirausaha_keywords = ['owner', 'founder', 'co-founder', 'ceo', 'wirausaha', 'entrepreneur', 'self-employed', 'freelance', 'pekerja lepas', 'business owner', 'self employed']
    
    if any(key in teks_gabungan for key in bumn_keywords): return "BUMN / BUMD"
    if any(key in teks_gabungan for key in pns_keywords): return "PNS / Pemerintahan"
    if any(key in teks_gabungan for key in pendidikan_keywords): return "Pendidikan / Akademisi"
    if any(key in teks_gabungan for key in wirausaha_keywords): return "Wirausaha / Freelance"
        
    if company == 'Tidak dicantumkan' and occupation == 'Tidak dicantumkan':
        return "Tidak Ada Data Pekerjaan"
    else:
        return "Swasta"

def main():
    global client 
    
    print("="*60)
    print("🚀 MEMULAI PROGRAM MASS-PROFILING ALUMNI UMM")
    print("="*60)
    
    token_awal = input("🔑 Masukkan API Token Apify Anda: ").strip()
    if not token_awal:
        print("Token tidak boleh kosong! Program dihentikan.")
        return
        
    client = ApifyClient(token_awal)
    
    print("\nMembaca file Excel...")
    try:
        df = pd.read_excel(FILE_INPUT)
    except FileNotFoundError:
        print(f"Error: File '{FILE_INPUT}' tidak ditemukan.")
        return
    except Exception as e:
        print(f"Error saat membaca Excel: {e}")
        return

    total_data = len(df)
    print(f"Total data di Excel: {total_data} baris.")

    try:
        mulai_baris = int(input(f"👉 Mulai dari baris ke berapa? (1 - {total_data}): "))
        jumlah_proses = int(input(f"👉 Berapa banyak data yang ingin diproses sekarang?: "))
    except ValueError:
        print("Harap masukkan angka yang valid!")
        return

    index_awal = mulai_baris - 1
    index_akhir = index_awal + jumlah_proses
    df_subset = df.iloc[index_awal:index_akhir]
    baris_akhir = mulai_baris + jumlah_proses - 1
    
    print(f"\nMemproses {len(df_subset)} data (Baris {mulai_baris} s/d {baris_akhir})...\n")
    file_output = f'data_${mulai_baris}_${baris_akhir}.csv'

    for step, (index, row) in enumerate(df_subset.iterrows(), start=1):
        nama_asli = row.get('Nama Lulusan', '')
        nim_asli = row.get('NIM', 'Tidak dicantumkan')
        thn_masuk = row.get('Tahun Masuk', 'Tidak dicantumkan')
        tgl_lulus = row.get('Tanggal Lulus', 'Tidak dicantumkan')
        fakultas = row.get('Fakultas', 'Tidak dicantumkan')
        prodi = row.get('Program Studi', 'Tidak dicantumkan')
        
        first_name, last_name = pisahkan_nama(nama_asli)
        
        print(f"\n" + "-"*50)
        print(f"🔄 PROGRESS : Data ke-{step} dari {len(df_subset)}")
        print(f"📍 EXCEL    : Mengerjakan baris ke-{index + 1}")
        
        if not first_name and not last_name:
            print(f"⚠️ INFO     : Baris kosong diabaikan.")
            continue
            
        print(f"👤 MENCARI  : {first_name} | {last_name}")

        run_input = {
            "firstName": first_name,
            "lastName": last_name,
            "profileScraperMode": "Full + email search",
            "strictSearch": False,
            "maxPages": 1
        }

        max_retries = 3
        attempt = 0
        dataset_items = None
        berhasil_konek = False

        while attempt < max_retries:
            try:
                run = client.actor("harvestapi/linkedin-profile-search-by-name").call(run_input=run_input)
                dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
                berhasil_konek = True
                break 
            except Exception as e:
                error_msg = str(e).lower()
                if 'credit' in error_msg or 'limit' in error_msg or '402' in error_msg or 'payment' in error_msg:
                    print(f"\n🛑 PERINGATAN: Saldo API habis!")
                    token_baru = input("👉 Masukkan Token BARU (atau 'exit'): ").strip()
                    if token_baru.lower() == 'exit': break 
                    elif token_baru:
                        client = ApifyClient(token_baru)
                        continue 
                if attempt < max_retries - 1:
                    time.sleep(3)
                attempt += 1

        if berhasil_konek and dataset_items:
            target_ketemu_umm = False
            for i, item in enumerate(dataset_items[:10]):
                school_info = str(item.get('school', '')).lower()
                education_info = str(item.get('education', '')).lower()
                summary_info = str(item.get('description', '')).lower()
                
                target_uni = "muhammadiyah malang"
                
                # --- FILTER KAMPUS: Hanya lanjut jika mengandung Muhammadiyah Malang ---
                if target_uni in school_info or target_uni in education_info or target_uni in summary_info:
                    
                    # === DEFENSIVE PROGRAMMING: CEGAH NULL DENGAN NILAI DEFAULT ===
                    headline = str(item.get('headline') or 'Tidak dicantumkan').strip()
                    url = item.get('url') or item.get('linkedinUrl') or 'Tidak dicantumkan'
                    
                    email_list = item.get('emails', [])
                    email_ditemukan = item.get('email') or (email_list[0].get('email', 'Tidak publik') if isinstance(email_list, list) and len(email_list) > 0 else 'Tidak publik')
                    
                    raw_lokasi = item.get('location')
                    lokasi_bersih = raw_lokasi.get('linkedinText', 'Tidak dicantumkan') if isinstance(raw_lokasi, dict) else (str(raw_lokasi) if raw_lokasi else 'Tidak dicantumkan')

                    # Inisialisasi Data Pekerjaan & Sosmed Kantor (Semua Anti-Null)
                    tempat_present, posisi_present, status_present, sosmed_present = "Tidak dicantumkan", "Tidak dicantumkan", "Tidak Ada Pekerjaan Aktif", "Tidak dicantumkan"
                    tempat_terakhir, posisi_terakhir, status_terakhir, sosmed_terakhir = "Tidak dicantumkan", "Tidak dicantumkan", "Belum Pernah Bekerja", "Tidak dicantumkan"
                    
                    pengalaman = item.get('experience') or item.get('currentPosition')
                    
                    if pengalaman and isinstance(pengalaman, list) and len(pengalaman) > 0:
                        # 1. PEKERJAAN PRESENT (Posisi Teratas)
                        pekerjaan_1 = pengalaman[0]
                        comp_name = str(pekerjaan_1.get('companyName') or 'Tidak dicantumkan').strip()
                        occ_name = str(pekerjaan_1.get('position') or 'Tidak dicantumkan').strip()
                        emp_type = str(pekerjaan_1.get('employmentType') or '').lower()
                        sosmed_1 = str(pekerjaan_1.get('companyLinkedinUrl') or 'Tidak dicantumkan')
                        
                        is_resign = False
                        end_date = pekerjaan_1.get('endDate')
                        if end_date and 'year' in end_date:
                            if end_date['year'] < 2026:
                                is_resign = True
                                comp_name = f"{comp_name} (Resign {end_date['year']})"
                                
                        if is_resign:
                            tempat_terakhir, posisi_terakhir, status_terakhir, sosmed_terakhir = comp_name, occ_name, klasifikasi_status(headline, comp_name, occ_name), sosmed_1
                        else:
                            tempat_present, posisi_present, status_present, sosmed_present = comp_name, occ_name, klasifikasi_status(headline, comp_name, occ_name), sosmed_1
                            
                            # 2. PEKERJAAN TERAKHIR (Posisi Kedua)
                            if len(pengalaman) > 1:
                                pekerjaan_2 = pengalaman[1]
                                comp_name_2 = str(pekerjaan_2.get('companyName') or 'Tidak dicantumkan').strip()
                                occ_name_2 = str(pekerjaan_2.get('position') or 'Tidak dicantumkan').strip()
                                sosmed_2 = str(pekerjaan_2.get('companyLinkedinUrl') or 'Tidak dicantumkan')
                                
                                end_date_2 = pekerjaan_2.get('endDate')
                                if end_date_2 and 'year' in end_date_2:
                                    comp_name_2 = f"{comp_name_2} (Resign {end_date_2['year']})"
                                    
                                tempat_terakhir, posisi_terakhir, status_terakhir, sosmed_terakhir = comp_name_2, occ_name_2, klasifikasi_status("", comp_name_2, occ_name_2), sosmed_2

                    # --- DATA AKHIR YANG AKAN DISIMPAN ---
                    hasil_baris = {
                        'Nama Lulusan': nama_asli, 
                        'NIM': nim_asli, 
                        'Tahun Masuk': thn_masuk, 
                        'Tanggal Lulus': tgl_lulus,
                        'Fakultas': fakultas, 
                        'Program Studi': prodi, 
                        'Linkedin': url, 
                        'Email': email_ditemukan,
                        'Alamat Bekerja': lokasi_bersih,
                        'Tempat Bekerja (Present)': tempat_present, 
                        'Posisi Jabatan (Present)': posisi_present, 
                        'Status Pekerjaan (Present)': status_present,
                        'Sosmed Kantor (Present)': sosmed_present,
                        'Tempat Bekerja (Terakhir)': tempat_terakhir, 
                        'Posisi Jabatan (Terakhir)': posisi_terakhir, 
                        'Status Pekerjaan (Terakhir)': status_terakhir,
                        'Sosmed Kantor (Terakhir)': sosmed_terakhir,
                        'Instagram': 'Tidak publik', 
                        'TikTok': 'Tidak publik', 
                        'Facebook': 'Tidak publik', 
                        'Nomor HP': 'Tidak publik'
                    }

                    # --- PROSES SIMPAN HANYA JIKA ALUMNI UMM ---
                    df_hasil = pd.DataFrame([hasil_baris])
                    if not os.path.isfile(file_output):
                        df_hasil.to_csv(file_output, index=False, mode='w', encoding='utf-8')
                    else:
                        df_hasil.to_csv(file_output, index=False, mode='a', header=False, encoding='utf-8')

                    target_ketemu_umm = True
                    print(f"   => ✅ DATA DISIMPAN: Alumni UMM terdeteksi.")
                    break 

            if not target_ketemu_umm:
                print(f"   => ❌ DIABAIKAN: Bukan Alumni UMM.")
        else:
            print(f"   => ❌ DIABAIKAN: Tidak ditemukan profil.")

    print(f"\n🎉 SELESAI! Hasil bersih alumni UMM tersimpan di: {file_output}")

if __name__ == '__main__':
    main()