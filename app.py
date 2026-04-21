import os
import uuid
import secrets
from datetime import date, timedelta
from urllib.parse import urlparse
from flask import Flask, Response, request, jsonify, make_response

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL', '')
ADMIN_USER   = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASS   = os.environ.get('ADMIN_PASSWORD', 'calitrain123')

# In-memory admin tokens {token: True}
admin_tokens = {}

if DATABASE_URL:
    print("✅ Using PostgreSQL database")
    import pg8000.native

    def get_conn():
        url = urlparse(DATABASE_URL)
        return pg8000.native.Connection(
            user=url.username, password=url.password,
            host=url.hostname, port=url.port or 5432,
            database=url.path.lstrip('/'), ssl_context=True
        )

    def init_db():
        conn = get_conn()
        conn.run('''CREATE TABLE IF NOT EXISTS progress (
            session_id TEXT NOT NULL, set_key TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE, saved_date DATE NOT NULL,
            PRIMARY KEY (session_id, set_key))''')
        conn.run('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
        # Default settings
        conn.run('''INSERT INTO settings (key, value) VALUES ('streak_required','7')
            ON CONFLICT (key) DO NOTHING''')
        conn.run('''INSERT INTO settings (key, value) VALUES ('manual_days_required','5')
            ON CONFLICT (key) DO NOTHING''')
        conn.run('''INSERT INTO settings (key, value) VALUES ('completion_pct','70')
            ON CONFLICT (key) DO NOTHING''')
        print("✅ PostgreSQL tables ready")

    def fetch_progress(session_id, today):
        conn = get_conn()
        rows = conn.run(
            'SELECT set_key, done FROM progress WHERE session_id = :sid AND saved_date = :d',
            sid=session_id, d=today)
        return [{'set_key': r[0], 'done': r[1]} for r in rows]

    def upsert_set(session_id, set_key, done, today):
        conn = get_conn()
        conn.run('''INSERT INTO progress (session_id, set_key, done, saved_date)
            VALUES (:sid, :k, :done, :d)
            ON CONFLICT (session_id, set_key)
            DO UPDATE SET done = EXCLUDED.done, saved_date = EXCLUDED.saved_date''',
            sid=session_id, k=set_key, done=done, d=today)

    def get_settings():
        conn = get_conn()
        rows = conn.run('SELECT key, value FROM settings')
        return {r[0]: r[1] for r in rows}

    def save_setting(key, value):
        conn = get_conn()
        conn.run('''INSERT INTO settings (key, value) VALUES (:k, :v)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value''',
            k=key, v=str(value))

else:
    print("⚠️  No DATABASE_URL — using SQLite")
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'progress.db')

    def get_conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        with get_conn() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS progress (
                session_id TEXT NOT NULL, set_key TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0, saved_date TEXT NOT NULL,
                PRIMARY KEY (session_id, set_key))''')
            conn.execute('''CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
            conn.execute("INSERT OR IGNORE INTO settings (key,value) VALUES ('streak_required','7')")
            conn.execute("INSERT OR IGNORE INTO settings (key,value) VALUES ('manual_days_required','5')")
            conn.execute("INSERT OR IGNORE INTO settings (key,value) VALUES ('completion_pct','70')")
            conn.commit()

    def fetch_progress(session_id, today):
        with get_conn() as conn:
            return conn.execute(
                'SELECT set_key, done FROM progress WHERE session_id=? AND saved_date=?',
                (session_id, today)).fetchall()

    def upsert_set(session_id, set_key, done, today):
        with get_conn() as conn:
            conn.execute('''INSERT OR REPLACE INTO progress (session_id, set_key, done, saved_date)
                VALUES (?,?,?,?)''', (session_id, set_key, int(done), today))
            conn.commit()

    def get_settings():
        with get_conn() as conn:
            rows = conn.execute('SELECT key, value FROM settings').fetchall()
            return {r['key']: r['value'] for r in rows}

    def save_setting(key, value):
        with get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)', (key, str(value)))
            conn.commit()

init_db()

# ── Helpers ──────────────────────────────────────────────────────────────────

def ensure_session(req, resp):
    sid = req.cookies.get('calitrain_session')
    if not sid:
        sid = str(uuid.uuid4())
        resp.set_cookie('calitrain_session', sid, max_age=365*24*3600)
    return sid

def is_admin(req):
    token = req.cookies.get('calitrain_admin')
    return token and token in admin_tokens

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ['index.html', 'index.html.html']:
        path = os.path.join(base, name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            resp = make_response(Response(content, mimetype='text/html'))
            ensure_session(request, resp)
            return resp
    return jsonify({'error': 'No index file found'}), 500

@app.route('/api/progress')
def get_progress():
    sid   = request.cookies.get('calitrain_session', str(uuid.uuid4()))
    today = str(date.today())
    rows  = fetch_progress(sid, today)
    completed = {row['set_key']: bool(row['done']) for row in rows}
    return jsonify({'completed': completed, 'date': today})

@app.route('/api/toggle', methods=['POST'])
def toggle_set():
    sid   = request.cookies.get('calitrain_session', str(uuid.uuid4()))
    today = str(date.today())
    data  = request.get_json()
    set_key = f"{data['day']}-{data['exercise']}-{data['set']}"
    upsert_set(sid, set_key, data['done'], today)
    return jsonify({'ok': True})

@app.route('/api/settings')
def api_settings():
    return jsonify(get_settings())

# ── Admin routes ──────────────────────────────────────────────────────────────

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('username') == ADMIN_USER and data.get('password') == ADMIN_PASS:
        token = secrets.token_hex(32)
        admin_tokens[token] = True
        resp = make_response(jsonify({'ok': True}))
        resp.set_cookie('calitrain_admin', token, max_age=3600, httponly=True)
        return resp
    return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    token = request.cookies.get('calitrain_admin')
    if token in admin_tokens:
        del admin_tokens[token]
    resp = make_response(jsonify({'ok': True}))
    resp.delete_cookie('calitrain_admin')
    return resp

@app.route('/api/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not is_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        data = request.get_json()
        allowed = ['streak_required', 'manual_days_required', 'completion_pct']
        for key in allowed:
            if key in data:
                save_setting(key, data[key])
        return jsonify({'ok': True})
    return jsonify(get_settings())

if __name__ == '__main__':
    app.run(debug=True)
