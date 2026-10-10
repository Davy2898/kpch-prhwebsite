# Kampong Chhnang Provincial Referral Hospital (KCNPRH) Website

This repository contains the full web application for Kampong Chhnang Provincial Referral Hospital.

- **Frontend**: Vue 3 + Vite
- **Backend**: Flask (Python) + SQLite
- **Admin Portal**: Integrated Flask Admin (`/admin`)

---

## Quick Start for Developers

The application is located in the `kcnprh-main/reach` directory.

### 1. Navigate to the App Folder
```bash
cd kcnprh-main/reach
```

### 2. Python Environment & Dependencies
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Install Node.js Dependencies
```bash
npm install
```

### 4. Run Backend & Frontend

Open two terminals:

**Terminal 1 (Backend - Flask):**
```bash
python run_local.py
```
> Runs on `http://127.0.0.1:5001`. On first run, it automatically copies the seeded database with all current posts, categories, and hospital details.

**Terminal 2 (Frontend - Vue Dev Server):**
```bash
npm run dev
```
> Runs on `http://localhost:5173/`. Open this URL in your browser.

---

### Admin Login
- URL: `http://localhost:5173/admin/login` (or `http://127.0.0.1:5001/admin/login`)
- Username: `admin`
- To reset admin password anytime:
  ```bash
  python reset_admin_password.py "YourPasswordHere"
  ```
