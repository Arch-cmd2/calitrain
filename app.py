import os
from flask import Flask, Response, make_response

app = Flask(__name__)

@app.route('/')
def index():
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ['index.html', 'index_html.html', 'templates/index.html']:
        path = os.path.join(base, name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return make_response(Response(content, mimetype='text/html'))
    return make_response(Response('index.html not found', status=500))

if __name__ == '__main__':
    app.run(debug=True)