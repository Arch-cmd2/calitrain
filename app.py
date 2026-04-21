import os
import uuid
from datetime import date
from flask import Flask, Response, request, jsonify, make_response

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
 
# ── Database helpers ─────────────────────────────────────────────────────────

if DATABASE_URL.startswith('postgres'):
    import psycopg2
    from psycopg2.extras import RealDictCursor

    def get_db():
        return psycopg2.connect(DATABASE_URL, sslmode='require')

    def init_db():
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS progress (
                        session_id TEXT NOT NULL,
                        set_key    TEXT NOT NULL,
                        done       BOOLEAN NOT NULL DEFAULT FALSE,
                        saved_date DATE NOT NULL,
                        PRIMARY KEY (session_id, set_key)
                    )
                ''')
            conn.commit()

    def fetch_progress(session_id, today):
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    'SELECT set_key, done FROM progress '
                    'WHERE session_id = %s AND saved_date = %s',
                    (session_id, today)
                )
                return cur.fetchall()

    def upsert_set(session_id, set_key, done, today):
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO progress (session_id, set_key, done, saved_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (session_id, set_key)
                    DO UPDATE SET done = EXCLUDED.done, saved_date = EXCLUDED.saved_date
                ''', (session_id, set_key, done, today))
            conn.commit()

else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'progress.db')

    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        with get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS progress (
                    session_id TEXT NOT NULL,
                    set_key    TEXT NOT NULL,
                    done       INTEGER NOT NULL DEFAULT 0,
                    saved_date TEXT NOT NULL,
                    PRIMARY KEY (session_id, set_key)
                )
            ''')
            conn.commit()

    def fetch_progress(session_id, today):
        with get_db() as conn:
            return conn.execute(
                'SELECT set_key, done FROM progress '
                'WHERE session_id = ? AND saved_date = ?',
                (session_id, today)
            ).fetchall()

    def upsert_set(session_id, set_key, done, today):
        with get_db() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO progress (session_id, set_key, done, saved_date)
                VALUES (?, ?, ?, ?)
            ''', (session_id, set_key, int(done), today))
            conn.commit()

init_db()

# ── Routes ───────────────────────────────────────────────────────────────────

def ensure_session(req, resp):
    sid = req.cookies.get('calitrain_session')
    if not sid:
        sid = str(uuid.uuid4())
        resp.set_cookie('calitrain_session', sid, max_age=365 * 24 * 3600)
    return sid

@app.route('/')
def index():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        os.path.join(base_dir, 'templates', 'index.html'),
        os.path.join(base_dir, 'index.html'),
        os.path.join(base_dir, 'index.html.html'),
    ]
    content = None
    for path in candidate_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            break

    if content is None:
        return make_response(
            jsonify({
                'error': 'index.html not found',
                'checked_paths': candidate_paths
            }),
            500
        )

    resp = make_response(Response(content, mimetype='text/html'))
    ensure_session(request, resp)
    return resp

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

if __name__ == '__main__':
    app.run(debug=True)
