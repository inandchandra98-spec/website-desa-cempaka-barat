# Website Pemerintah Desa Cempaka Barat — starter full-stack

Paket ini adalah fondasi aplikasi Flask + SQLite untuk website publik dan panel admin. Beranda memakai gaya glassmorphism biru/teal. Konten yang dibuat lewat panel admin disimpan di database dan dapat tampil di halaman publik. Ini **belum boleh dianggap siap produksi** sebelum konfigurasi server, pemeriksaan keamanan, verifikasi data, dan pengujian tambahan dilakukan.

## Fitur yang sudah diimplementasikan
- Beranda responsif dan halaman publik: profil, pemerintahan, berita, agenda, galeri, layanan, statistik, APBDes, dokumen, kontak/pengaduan, pencarian, dan 404.
- Panel admin dengan dashboard, CRUD generik untuk berita, perangkat desa, galeri, layanan, dokumen, agenda, statistik, halaman informasi, transparansi APBDes.
- Login memakai hash kata sandi Werkzeug; sesi HTTP-only dan SameSite; token CSRF untuk POST; peran `superadmin`/`admin`/`editor` tersedia pada skema.
- Form kontak/pengaduan tersimpan di SQLite; status pengaduan dapat diperbarui admin.
- Pengaturan identitas desa, unggahan dengan batas ukuran dan ekstensi, log aktivitas, endpoint kesehatan `/api/health`.
- Beranda HTML lama disimpan sebagai `referensi-beranda.html` untuk acuan dan perbandingan.

## Belum selesai / perlu konfigurasi
- SQLite cocok untuk prototipe atau satu server kecil; evaluasi PostgreSQL untuk multi-pengguna/produksi.
- Pembatasan percobaan login/rate limiting, alur reset kata sandi, MFA, manajemen sesi yang lebih ketat, pemindaian file unggahan, dan pengujian penetrasi belum diterapkan.
- Role `editor` tersimpan tetapi aturan otorisasi per-fitur belum sepenuhnya dibedakan dari admin.
- Upload dokumen masuk ke folder publik; **jangan unggah dokumen berisi data pribadi/rahasia**. Perlu storage privat dan endpoint unduh berotorisasi jika dibutuhkan.
- Konten dinamis saat ini ditampilkan sebagai teks biasa; belum ada editor kaya, pagination penuh, alur persetujuan konten, atau ekspor/backup otomatis terjadwal.
- Weather real-time, video profil, peta, surat otomatis/PDF, statistik interaktif, dan integrasi layanan kependudukan belum dihubungkan.
- Foto latar berasal dari Unsplash dan membutuhkan internet. Ganti dengan foto desa resmi yang punya izin penggunaan.
- Verifikasi nama perangkat desa, statistik, APBDes, alamat, dan semua data sebelum publikasi. Isi data contoh hanya melalui panel admin setelah ada data resmi.

## Instalasi di Windows 10/11
1. Pasang Python 3.11 atau lebih baru dari python.org dan centang **Add Python to PATH**.
2. Ekstrak folder proyek, lalu buka Command Prompt/PowerShell pada folder `cempaka_barat_app`.
3. Buat virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   Jika PowerShell memblokir aktivasi, gunakan Command Prompt: `.venv\Scripts\activate.bat`.
4. Instal dependensi: `python -m pip install -r requirements.txt`
5. Salin `.env.example` menjadi `.env`, lalu buat `SECRET_KEY` acak yang panjang. Aplikasi ini tidak otomatis membaca `.env`; masukkan variabel ke lingkungan Windows atau gunakan pengelola environment di server. Jangan commit secret ke Git.
6. Buat database: `python init_db.py`
7. Buat akun admin pertama: `python create_admin.py` (kata sandi minimal 12 karakter; tidak ada akun/kata sandi bawaan).
8. Jalankan: `python app.py`
9. Buka `http://127.0.0.1:5000`. Panel admin: `http://127.0.0.1:5000/admin`.
10. Setelah berhasil masuk, atur identitas desa dan buat konten dengan data resmi.

## Variabel lingkungan
`SECRET_KEY`, `DATABASE_PATH`, `UPLOAD_DIR`, `HOST`, `PORT`, `FLASK_DEBUG`, `COOKIE_SECURE`. Jangan gunakan secret contoh di produksi. Gunakan HTTPS dan set `COOKIE_SECURE=1` ketika berada di belakang HTTPS. Jalankan dengan WSGI server yang sesuai, bukan development server Flask, untuk deployment publik.

## Backup dan pemulihan
- Hentikan aplikasi terlebih dahulu agar file database tidak sedang ditulis.
- Salin `data/cempaka.sqlite3` dan folder `static/uploads/` ke media backup terenkripsi dengan akses terbatas.
- Untuk pemulihan, hentikan aplikasi, pulihkan kedua bagian ke lokasi yang sama, cek izin file, lalu jalankan `python init_db.py` dan uji `/api/health`.
- Buat backup berkala di server produksi dan uji proses restore; salinan yang belum pernah diuji belum dianggap backup andal.

## Pengujian
Jalankan `python -m unittest discover -s tests -v`. Pengujian ini pemeriksaan smoke dasar, bukan audit keamanan penuh. Periksa juga alur login, CRUD, CSRF, unggahan, akses role, tampilan mobile, dan log server sebelum dipakai publik.

## API konten
- `GET /api/content/<kind>` — daftar konten publik yang berstatus published; mendukung `?q=kata-kunci`.
- `GET /api/content/<kind>/<id>` — detail konten publik.
- `POST /api/content/<kind>` — membuat konten (admin login + header `X-CSRF-Token`). JSON contoh: `{"title":"Judul","summary":"Ringkasan","body":"Isi","status":"draft"}`.
- `PUT`/`PATCH /api/content/<kind>/<id>` — memperbarui konten (admin login + CSRF header).
- `DELETE /api/content/<kind>/<id>` — menghapus konten (admin login + CSRF header).
- `GET /api/health` — pemeriksaan koneksi database.

Untuk API yang mengubah data, ambil token CSRF dari sesi admin pada halaman admin dan kirim sebagai `X-CSRF-Token`. Endpoint mutasi API belum memiliki rate limiting khusus; jangan mengekspos ke internet sebelum hardening dan pengujian keamanan.
