@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -m venv .venv
  if errorlevel 1 pause & exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 echo Gagal memasang dependensi. Periksa koneksi internet dan Python. & pause & exit /b 1
python init_db.py
python app.py
pause
