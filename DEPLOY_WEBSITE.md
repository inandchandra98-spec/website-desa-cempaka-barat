# Menjadikan Website Desa Cempaka Barat online

Proyek ini adalah **website berbasis web** (dibuka melalui browser), bukan aplikasi desktop Windows. Flask diperlukan sebagai backend agar panel admin, login, dan penyimpanan konten tetap berfungsi.

## Perbedaan mode lokal dan website online
- `http://127.0.0.1:5000` hanya dapat dibuka dari komputer yang menjalankan server. Ini untuk pratinjau/pengembangan.
- Agar bisa diakses masyarakat, proyek harus diunggah ke hosting/server yang mendukung Python/Flask, diberi domain (opsional pada tahap awal), dan dilindungi HTTPS.
- Mengunggah satu file HTML saja tidak akan mengaktifkan backend, login aman, database, atau panel admin dinamis.

## File deployment
`Procfile` menjalankan website dengan Gunicorn pada hosting yang mendukung perintah Procfile. `requirements.txt` menyertakan Gunicorn. Ikuti petunjuk dari penyedia hosting untuk mengatur variabel lingkungan dan domain.

## Variabel lingkungan yang wajib diatur di server
- `SECRET_KEY`: rahasia acak panjang, berbeda dari contoh, jangan dipublikasikan.
- `COOKIE_SECURE=1`: aktifkan setelah HTTPS berjalan.
- `DATABASE_PATH`: arah ke file SQLite pada penyimpanan persisten.
- `UPLOAD_DIR`: arah ke folder unggahan yang persisten.
- `FLASK_DEBUG=0`.

**Penting:** hosting yang menghapus filesystem saat deploy/restart tidak boleh menyimpan database dan unggahan hanya di filesystem sementara. Gunakan disk persisten atau database/storage terkelola. Uji backup dan pemulihan.

## Langkah ringkas publikasi
1. Pilih hosting Python/Flask yang menyediakan filesystem persisten atau konfigurasi database/storage terkelola.
2. Unggah repositori/proyek ini ke hosting.
3. Pasang dependensi dari `requirements.txt`; perintah start: `gunicorn app:app --bind 0.0.0.0:$PORT`.
4. Atur variabel lingkungan rahasia dan lokasi database/unggahan pada dashboard hosting.
5. Jalankan migrasi/inisialisasi database sesuai panduan proyek. Buat akun admin lewat `python create_admin.py` di lingkungan server/console hosting yang aman.
6. Aktifkan HTTPS dan `COOKIE_SECURE=1`, atur domain, lalu uji website publik dan `/admin`.
7. Jalankan pengujian, tinjau log server, dan pastikan backup otomatis berfungsi sebelum menerima data warga.

## Status
Berkas deployment telah disiapkan, tetapi publikasi belum dilakukan: domain dan akun hosting harus disediakan oleh pemilik website. Website belum bisa diakses publik sampai proses deploy benar-benar dijalankan. Lakukan hardening dan pengujian keamanan sebelum penggunaan resmi.
