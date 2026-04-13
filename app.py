import os
from flask import Flask, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/")
def index():
    return send_from_directory(os.path.join(BASE_DIR, "templates"), "index.html")

if __name__ == "__main__":
    app.run(debug=True)
