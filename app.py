import os
import uuid
from flask import Flask, Response, request, jsonify, make_response

app = Flask(__name__)


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
    # Frontend now stores progress in localStorage (no backend DB required).
    return jsonify({'completed': {}, 'date': ''})

@app.route('/api/toggle', methods=['POST'])
def toggle_set():
    # No-op endpoint kept for backwards compatibility.
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)
