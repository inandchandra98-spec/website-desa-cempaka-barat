import getpass, re
from app import db, init_db, now
from werkzeug.security import generate_password_hash

def main():
    init_db(); username=input('Username admin (3-40 karakter): ').strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,40}',username): raise SystemExit('Username tidak valid.')
    password=getpass.getpass('Kata sandi (minimal 12 karakter): ')
    if len(password)<12: raise SystemExit('Kata sandi harus minimal 12 karakter.')
    confirm=getpass.getpass('Ulangi kata sandi: ')
    if password!=confirm: raise SystemExit('Kata sandi tidak cocok.')
    with db() as con:
        if con.execute('SELECT 1 FROM admins LIMIT 1').fetchone(): role='admin'
        else: role='superadmin'
        try: con.execute('INSERT INTO admins(username,password_hash,role,created_at) VALUES(?,?,?,?)',(username,generate_password_hash(password),role,now()))
        except Exception as exc: raise SystemExit(f'Gagal membuat admin: {exc}')
    print(f'Akun {username} dibuat dengan peran {role}.')
if __name__=='__main__': main()
