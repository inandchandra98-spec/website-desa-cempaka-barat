# Status implementasi dan pengujian

Tanggal paket: 22 Oktober 2026.

## Pemeriksaan yang berhasil dilakukan di lingkungan pembuat
- Kompilasi sintaks Python untuk `app.py`, `init_db.py`, `create_admin.py`, dan `tests/test_app.py`: **LULUS** (`py_compile`).
- Parsing dasar semua 14 template HTML/Jinja dengan parser HTML: **LULUS**.
- Struktur proyek, stylesheet, JavaScript, dokumentasi, dan file konfigurasi contoh: **TERSEDIA**.

## Pemeriksaan yang belum dapat dijalankan
- Smoke test Flask (beranda, login, CRUD, kontak, endpoint API, dan database): **BELUM TERVERIFIKASI** karena modul Flask tidak terpasang di lingkungan pembuat dan akses jaringan untuk memasang dependensi tidak tersedia.
- Uji lintas browser/ukuran layar, konsol browser, CSRF end-to-end, unggahan file, uji keamanan, dan uji beban: **BELUM DILAKUKAN**.

## Sebelum dipakai secara nyata
1. Instal dependensi dari `requirements.txt` pada komputer/server yang memiliki akses paket.
2. Jalankan `python -m unittest discover -s tests -v` dan perbaiki semua kegagalan.
3. Uji manual seluruh alur dan endpoint API.
4. Ganti secret, aktifkan HTTPS, tinjau CSP/session, tambahkan rate limiting, aturan izin per peran, pemindaian unggahan, dan penyimpanan privat untuk dokumen sensitif.
5. Verifikasi seluruh data resmi desa dan foto yang memiliki izin.
6. Siapkan backup terjadwal, uji pemulihan, dan minta tinjauan keamanan sebelum membuka website ke internet.
