import os
from flask import Flask, Response

app = Flask(__name__)

@app.route("/")
def index():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html")

if __name__ == "__main__":
    app.run(debug=True)
