# 🧾 QR Meal Tracker

A desktop application for tracking meal pickups using QR codes. Designed for institutions like training centers, restaurants, or schools that provide daily meals and need per-customer tracking.

Built with **Python + Tkinter**, featuring an Arabic user interface, local SQLite storage, and Excel export support.

---

## 🚀 Features

- 📸 Read QR codes via USB scanner
- 🧠 Automatically log one meal per customer per day
- 📆 Track daily and monthly pickups
- 📊 View monthly statistics in the app
- 💾 Export reports to Excel
- 🎨 Modern Arabic UI with logo and icons
- 🔒 Offline/local storage (SQLite)

---

## 🖥️ Run Locally (Developer Mode)

### 1. Clone the repo

```bash
git clone https://github.com/iq5sa/QR-Meal-Tracker.git
cd qr-meal-tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If the file is missing, install manually:

```bash
pip install pillow openpyxl pyinstaller
```

### 4. Run the app

```bash
python app.py
```
