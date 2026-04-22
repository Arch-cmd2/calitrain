# CALITRAIN 🌞 — Summer Body Edition

A personal workout web app built with Flask. Access it from any device, anywhere.

---

## 📁 Project Structure

```
calitrain/
├── app.py              ← Flask server (main file)
├── requirements.txt    ← Python dependencies
├── Procfile            ← For cloud deployment
├── README.md           ← This file
└── templates/
    └── index.html      ← The full workout app UI
```

---

## 🖥️ Run Locally

### 1. Install Python (if you haven't)
Download from https://python.org (version 3.8 or higher)

### 2. Open a terminal in this folder, then run:

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Start the app
python app.py
```

### 3. Open your browser and go to:
```
http://localhost:5000
```

---

## 🌐 Deploy Online (Free) — Render.com

Access your app from any phone or browser, anywhere in the world.

### Steps:
1. Create a free account at https://render.com
2. Upload this folder to a GitHub repository
   - Go to https://github.com → New repository → Upload files
3. In Render: **New → Web Service → Connect your GitHub repo**
4. Set these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3
5. Click **Deploy** — you'll get a public URL like `https://calitrain.onrender.com`

---

## 🚂 Deploy Online (Free) — Railway.app

1. Create a free account at https://railway.app
2. Click **New Project → Deploy from GitHub repo**
3. Connect your repo — Railway auto-detects the Procfile
4. Done! You'll get a public URL instantly.

---

## 📱 Tips
- The app is mobile-friendly — bookmark it on your phone's home screen
- All workout progress is stored in your browser session
- No database needed — everything runs in the browser
