import os, re, sqlite3, secrets, logging
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('DATABASE_PATH', BASE / 'data' / 'cempaka.sqlite3'))
UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', BASE / 'static' / 'uploads'))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
CONTENT_TYPES = {
 'news':'Berita', 'staff':'Perangkat Desa', 'gallery':'Galeri', 'services':'Layanan Publik',
 'documents':'Dokumen Publik', 'agenda':'Agenda', 'stats':'Statistik Desa', 'pages':'Halaman Informasi', 'budgets':'Transparansi APBDes'
}
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-only-change-this-secret-before-deployment'
app.config.update(MAX_CONTENT_LENGTH=8*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0') == '1')
UPLOAD_DIR.mkdir(parents=True, exist_ok=True); DB_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO)

SCHEMA = '''
CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'admin', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entries(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, title TEXT NOT NULL, slug TEXT, summary TEXT DEFAULT '', body TEXT DEFAULT '', image TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'published', metadata TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_entries_kind_status ON entries(kind,status);
CREATE TABLE IF NOT EXISTS submissions(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, name TEXT NOT NULL, contact TEXT DEFAULT '', subject TEXT NOT NULL, message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'baru', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(admin_id) REFERENCES admins(id));
'''
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def db():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; conn.execute('PRAGMA foreign_keys=ON'); return conn
def init_db():
    with db() as con:
        con.executescript(SCHEMA)
        if con.execute('SELECT COUNT(*) FROM settings').fetchone()[0] == 0:
            con.executemany('INSERT INTO settings(key,value) VALUES(?,?)', [
              ('village_name','Desa Cempaka Barat'),('district','Kecamatan Sungkai Utara'),('regency','Kabupaten Lampung Utara'),
              ('tagline','Maju Bersama, Sejahtera untuk Semua'),('address','Alamat kantor desa perlu dilengkapi'),('phone',''),('email',''),
              ('population',''),('families',''),('area',''),('logo','')])

def csrf_token():
    if '_csrf' not in session: session['_csrf'] = secrets.token_urlsafe(24)
    return session['_csrf']
app.jinja_env.globals['csrf_token'] = csrf_token
app.jinja_env.globals['content_types'] = CONTENT_TYPES
@app.before_request
def protect_post():
    if request.method == 'POST':
        sent = request.form.get('_csrf') or request.headers.get('X-CSRF-Token')
        if not sent or not secrets.compare_digest(str(sent), str(session.get('_csrf',''))): abort(400, 'Token keamanan tidak valid. Muat ulang halaman lalu coba kembali.')
@app.after_request
def security_headers(resp):
    resp.headers['X-Content-Type-Options']='nosniff'; resp.headers['X-Frame-Options']='SAMEORIGIN'; resp.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    resp.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    resp.headers['Content-Security-Policy']="default-src 'self' https: data:; img-src 'self' https: data:; style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'"
    return resp

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'): return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper
def log_action(action, detail):
    with db() as con: con.execute('INSERT INTO audit_logs(admin_id,action,detail,created_at) VALUES(?,?,?,?)',(session.get('admin_id'),action,detail[:300],now()))
def get_settings():
    with db() as con: return {r['key']:r['value'] for r in con.execute('SELECT key,value FROM settings')}
def entries(kind=None, status='published', limit=None):
    sql='SELECT * FROM entries'; params=[]; where=[]
    if kind: where.append('kind=?'); params.append(kind)
    if status: where.append('status=?'); params.append(status)
    if where: sql+=' WHERE '+' AND '.join(where)
    sql+=' ORDER BY updated_at DESC'
    if limit: sql+=' LIMIT ?'; params.append(limit)
    with db() as con: return con.execute(sql,params).fetchall()
@app.route('/')
def home():
    return render_template('home.html', settings=get_settings(), news=entries('news',limit=3), staff=entries('staff',limit=6), services=entries('services',limit=8), gallery=entries('gallery',limit=3), stats=entries('stats',limit=6))
@app.route('/halaman/<slug>')
def public_page(slug):
    mapping={'profil':'pages','sejarah':'pages','visi-misi':'pages','pemerintahan':'staff','berita':'news','pengumuman':'news','agenda':'agenda','galeri':'gallery','layanan':'services','statistik':'stats','apbdes':'budgets','dokumen':'documents'}
    kind=mapping.get(slug)
    if not kind: return render_template('404.html',settings=get_settings()),404
    items=entries(kind,limit=100)
    if slug in ('profil','sejarah','visi-misi'): items=[x for x in items if x['slug']==slug] or items
    return render_template('listing.html',settings=get_settings(),slug=slug,kind=kind,items=items,title=slug.replace('-',' ').title())
@app.route('/kontak', methods=['GET','POST'])
def contact():
    if request.method=='POST':
        name=request.form.get('name','').strip(); contact=request.form.get('contact','').strip(); subject=request.form.get('subject','').strip(); message=request.form.get('message','').strip(); kind=request.form.get('kind','kontak')
        if not name or not subject or len(message)<8: flash('Lengkapi nama, subjek, dan pesan minimal 8 karakter.','error')
        elif len(name)>100 or len(subject)>160 or len(message)>4000 or len(contact)>150: flash('Ada isian yang melebihi batas panjang.','error')
        else:
            with db() as con: con.execute('INSERT INTO submissions(kind,name,contact,subject,message,created_at) VALUES(?,?,?,?,?,?)',(kind,name,contact,subject,message,now()))
            flash('Pesan berhasil dikirim. Terima kasih.','success'); return redirect(url_for('contact'))
    return render_template('contact.html',settings=get_settings())
@app.route('/cari')
def search():
    q=request.args.get('q','').strip()[:100]; found=[]
    if q:
        with db() as con: found=con.execute("SELECT * FROM entries WHERE status='published' AND (title LIKE ? OR summary LIKE ? OR body LIKE ?) ORDER BY updated_at DESC LIMIT 50",(f'%{q}%',f'%{q}%',f'%{q}%')).fetchall()
    return render_template('search.html',settings=get_settings(),q=q,items=found)
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('admin_id'): return redirect(url_for('admin_dashboard'))
    if request.method=='POST':
        username=request.form.get('username','').strip(); password=request.form.get('password','')
        with db() as con: user=con.execute('SELECT * FROM admins WHERE username=?',(username,)).fetchone()
        if user and check_password_hash(user['password_hash'],password):
            session.clear(); session['admin_id']=user['id']; session['username']=user['username']; session['role']=user['role']; csrf_token(); log_action('login','Login admin berhasil'); return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('Nama pengguna atau kata sandi salah.','error')
    return render_template('login.html',settings=get_settings())
@app.route('/logout',methods=['POST'])
@admin_required
def logout():
    log_action('logout','Logout admin'); session.clear(); flash('Anda telah keluar.','success'); return redirect(url_for('home'))
@app.route('/admin')
@admin_required
def admin_dashboard():
    with db() as con:
        counts={k:con.execute('SELECT COUNT(*) FROM entries WHERE kind=?',(k,)).fetchone()[0] for k in CONTENT_TYPES}
        counts['submissions']=con.execute('SELECT COUNT(*) FROM submissions WHERE status="baru"').fetchone()[0]
        logs=con.execute('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10').fetchall()
    return render_template('admin.html',settings=get_settings(),counts=counts,logs=logs,section='dashboard')
@app.route('/admin/konten/<kind>')
@admin_required
def admin_content(kind):
    if kind not in CONTENT_TYPES: abort(404)
    q=request.args.get('q','').strip()[:100]
    with db() as con:
        if q: rows=con.execute('SELECT * FROM entries WHERE kind=? AND (title LIKE ? OR summary LIKE ?) ORDER BY updated_at DESC',(kind,f'%{q}%',f'%{q}%')).fetchall()
        else: rows=con.execute('SELECT * FROM entries WHERE kind=? ORDER BY updated_at DESC',(kind,)).fetchall()
    return render_template('admin_content.html',settings=get_settings(),kind=kind,kind_label=CONTENT_TYPES[kind],rows=rows,q=q,section=kind)
@app.route('/admin/konten/<kind>/baru',methods=['GET','POST'])
@app.route('/admin/konten/<kind>/<int:item_id>/edit',methods=['GET','POST'])
@admin_required
def edit_content(kind,item_id=None):
    if kind not in CONTENT_TYPES: abort(404)
    item=None
    if item_id:
        with db() as con: item=con.execute('SELECT * FROM entries WHERE id=? AND kind=?',(item_id,kind)).fetchone()
        if not item: abort(404)
    if request.method=='POST':
        title=request.form.get('title','').strip(); slug=request.form.get('slug','').strip(); summary=request.form.get('summary','').strip(); body=request.form.get('body','').strip(); status=request.form.get('status','published'); metadata=request.form.get('metadata','').strip(); image=(item['image'] if item else '')
        if not title or len(title)>200 or len(summary)>600 or len(body)>12000: flash('Judul wajib diisi; periksa batas panjang kolom.','error')
        elif status not in ('draft','published'): flash('Status tidak valid.','error')
        else:
            f=request.files.get('image')
            if f and f.filename:
                filename=secure_filename(f.filename); ext=filename.rsplit('.',1)[-1].lower() if '.' in filename else ''
                if ext not in ALLOWED_EXTENSIONS: flash('Jenis file tidak diizinkan.','error'); return render_template('edit_content.html',settings=get_settings(),kind=kind,kind_label=CONTENT_TYPES[kind],item=item)
                filename=f'{secrets.token_hex(8)}_{filename}'; f.save(UPLOAD_DIR/filename); image='/static/uploads/'+filename
            with db() as con:
                if item: con.execute('UPDATE entries SET title=?,slug=?,summary=?,body=?,image=?,status=?,metadata=?,updated_at=? WHERE id=?',(title,slug,summary,body,image,status,metadata,now(),item_id)); action='edit'
                else: con.execute('INSERT INTO entries(kind,title,slug,summary,body,image,status,metadata,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(kind,title,slug,summary,body,image,status,metadata,now(),now())); action='create'
            log_action(action,f'{CONTENT_TYPES[kind]}: {title}'); flash('Konten berhasil disimpan.','success'); return redirect(url_for('admin_content',kind=kind))
    return render_template('edit_content.html',settings=get_settings(),kind=kind,kind_label=CONTENT_TYPES[kind],item=item)
@app.route('/admin/konten/<kind>/<int:item_id>/hapus',methods=['POST'])
@admin_required
def delete_content(kind,item_id):
    if kind not in CONTENT_TYPES: abort(404)
    with db() as con: item=con.execute('SELECT title FROM entries WHERE id=? AND kind=?',(item_id,kind)).fetchone(); con.execute('DELETE FROM entries WHERE id=? AND kind=?',(item_id,kind))
    if item: log_action('delete',f'{CONTENT_TYPES[kind]}: {item["title"]}'); flash('Konten dihapus.','success')
    return redirect(url_for('admin_content',kind=kind))
@app.route('/admin/pengaduan')
@admin_required
def admin_submissions():
    with db() as con: rows=con.execute('SELECT * FROM submissions ORDER BY created_at DESC LIMIT 300').fetchall()
    return render_template('admin_submissions.html',settings=get_settings(),rows=rows,section='submissions')
@app.route('/admin/pengaduan/<int:item_id>/status',methods=['POST'])
@admin_required
def update_submission(item_id):
    status=request.form.get('status','diproses')
    if status not in ('baru','diproses','selesai'): abort(400)
    with db() as con: con.execute('UPDATE submissions SET status=? WHERE id=?',(status,item_id))
    log_action('submission-status',f'Pengaduan #{item_id}: {status}'); flash('Status pengaduan diperbarui.','success'); return redirect(url_for('admin_submissions'))
@app.route('/admin/pengaturan',methods=['GET','POST'])
@admin_required
def admin_settings():
    if request.method=='POST':
        allowed=['village_name','district','regency','tagline','address','phone','email','population','families','area']
        with db() as con:
            for key in allowed:
                value=request.form.get(key,'').strip()
                if len(value)>500: flash(f'Nilai {key} terlalu panjang.','error'); return redirect(url_for('admin_settings'))
                con.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,value))
        log_action('settings','Pengaturan identitas website diperbarui'); flash('Pengaturan disimpan.','success'); return redirect(url_for('admin_settings'))
    return render_template('admin_settings.html',settings=get_settings(),section='settings')
@app.route('/admin/pengguna',methods=['GET','POST'])
@admin_required
def admin_users():
    if session.get('role')!='superadmin': abort(403)
    if request.method=='POST':
        username=request.form.get('username','').strip(); password=request.form.get('password',''); role=request.form.get('role','admin')
        if not re.fullmatch(r'[A-Za-z0-9_.-]{3,40}',username) or len(password)<12 or role not in ('admin','editor','superadmin'):
            flash('Username 3–40 karakter; kata sandi minimal 12 karakter.','error')
        else:
            try:
                with db() as con: con.execute('INSERT INTO admins(username,password_hash,role,created_at) VALUES(?,?,?,?)',(username,generate_password_hash(password),role,now()))
                log_action('create-admin',f'Membuat pengguna {username}'); flash('Pengguna admin dibuat.','success')
            except sqlite3.IntegrityError: flash('Username sudah digunakan.','error')
    with db() as con: users=con.execute('SELECT id,username,role,created_at FROM admins ORDER BY id').fetchall()
    return render_template('admin_users.html',settings=get_settings(),users=users,section='users')
@app.route('/api/content/<kind>', methods=['GET','POST'])
def api_content_collection(kind):
    if kind not in CONTENT_TYPES: abort(404)
    if request.method == 'GET':
        q=request.args.get('q','').strip()[:100]
        sql='SELECT id,kind,title,slug,summary,body,image,status,metadata,created_at,updated_at FROM entries WHERE kind=?'
        params=[kind]
        if not session.get('admin_id'): sql+=" AND status='published'"
        if q: sql+=' AND (title LIKE ? OR summary LIKE ?)'; params.extend([f'%{q}%',f'%{q}%'])
        sql+=' ORDER BY updated_at DESC LIMIT 100'
        with db() as con: rows=con.execute(sql,params).fetchall()
        return jsonify(items=[dict(row) for row in rows])
    if not session.get('admin_id'): abort(403)
    data=request.get_json(silent=True) or {}
    title=str(data.get('title','')).strip(); summary=str(data.get('summary','')).strip(); body=str(data.get('body','')).strip()
    if not title or len(title)>200 or len(summary)>600 or len(body)>12000: return jsonify(error='Judul wajib diisi dan panjang kolom harus valid.'),400
    status=data.get('status','draft')
    if status not in ('draft','published'): return jsonify(error='Status tidak valid.'),400
    with db() as con:
        cur=con.execute('INSERT INTO entries(kind,title,slug,summary,body,status,metadata,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',(kind,title,str(data.get('slug',''))[:160],summary,body,status,str(data.get('metadata',''))[:2000],now(),now()))
        item=con.execute('SELECT * FROM entries WHERE id=?',(cur.lastrowid,)).fetchone()
    log_action('api-create',f'{CONTENT_TYPES[kind]}: {title}')
    return jsonify(item=dict(item)),201

@app.route('/api/content/<kind>/<int:item_id>', methods=['GET','PUT','PATCH','DELETE'])
def api_content_item(kind,item_id):
    if kind not in CONTENT_TYPES: abort(404)
    with db() as con: item=con.execute('SELECT * FROM entries WHERE id=? AND kind=?',(item_id,kind)).fetchone()
    if not item: abort(404)
    if request.method=='GET':
        if item['status']!='published' and not session.get('admin_id'): abort(404)
        return jsonify(item=dict(item))
    if not session.get('admin_id'): abort(403)
    if request.method=='DELETE':
        with db() as con: con.execute('DELETE FROM entries WHERE id=? AND kind=?',(item_id,kind))
        log_action('api-delete',f'{CONTENT_TYPES[kind]} #{item_id}')
        return jsonify(deleted=True,id=item_id)
    data=request.get_json(silent=True) or {}
    title=str(data.get('title',item['title'])).strip(); summary=str(data.get('summary',item['summary'])).strip(); body=str(data.get('body',item['body'])).strip(); status=data.get('status',item['status'])
    if not title or len(title)>200 or len(summary)>600 or len(body)>12000 or status not in ('draft','published'): return jsonify(error='Data tidak valid.'),400
    with db() as con:
        con.execute('UPDATE entries SET title=?,slug=?,summary=?,body=?,status=?,metadata=?,updated_at=? WHERE id=? AND kind=?',(title,str(data.get('slug',item['slug']))[:160],summary,body,status,str(data.get('metadata',item['metadata']))[:2000],now(),item_id,kind))
        updated=con.execute('SELECT * FROM entries WHERE id=?',(item_id,)).fetchone()
    log_action('api-update',f'{CONTENT_TYPES[kind]}: {title}')
    return jsonify(item=dict(updated))

@app.route('/api/health')
def health():
    try:
        with db() as con: con.execute('SELECT 1').fetchone()
        return jsonify(status='ok',database='connected')
    except sqlite3.Error: return jsonify(status='error',database='unavailable'),503
@app.errorhandler(404)
def not_found(e): return render_template('404.html',settings=get_settings()),404
@app.errorhandler(400)
def bad_request(e): return render_template('error.html',settings=get_settings(),code=400,message=getattr(e,'description','Permintaan tidak valid.')),400
@app.errorhandler(403)
def forbidden(e): return render_template('error.html',settings=get_settings(),code=403,message='Anda tidak memiliki izin untuk membuka halaman ini.'),403

if __name__ == '__main__':
    init_db()
    app.run(host=os.environ.get('HOST','127.0.0.1'),port=int(os.environ.get('PORT','5000')),debug=os.environ.get('FLASK_DEBUG','0')=='1')
