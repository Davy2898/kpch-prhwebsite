# Kampong Chhnang PRH Website

Vue is the public frontend. Flask provides the API, admin panel, uploads, and production server.

## Local Setup

Navigate to the project directory:

```bash
cd kcnprh-main/reach
```

### Option A: Standard Python (Recommended for any OS)
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
npm install
```

### Option B: Using uv
```powershell
uv venv .venv-win --python 3.12
uv pip install -r requirements.txt --python .venv-win\Scripts\python.exe
npm install
```

> **Note on Database**: `reach_seed.sqlite3` is included. When `run_local.py` runs for the first time, it automatically sets up `instance/reach.sqlite3` with all pre-existing hospital posts, categories, and settings.

## Local Development

Start the Flask backend first (Terminal 1):

```bash
python run_local.py
```

Start the Vue frontend in a second terminal:

```powershell
npm run dev
```

Open only the Vue frontend:

```text
http://localhost:5173/
```

Admin is served by Flask:

```text
http://localhost:5001/admin/login
```

## Admin Password

```powershell
.\.venv-win\Scripts\python.exe reset_admin_password.py "Admin@2026"
```

Username:

```text
admin
```

## Production Build

Run this before hosting or committing built frontend changes:

```powershell
npm run build
```

This writes:

- `app/static/vue/assets/app.js`
- `app/static/vue/assets/app.css`
- `app/static/css/tailwind.css`

## Production Environment

Set real values on the host. Do not commit `.env`.

```text
FLASK_ENV=production
SECRET_KEY=<long-random-secret>
DATABASE_URL=<postgres-url>
TELEGRAM_BOT_TOKEN=<optional>
TELEGRAM_CHAT_ID=<optional>
```

If `DATABASE_URL` is not set, the app uses local SQLite. For real hosting, use PostgreSQL or another managed database.

## Security Notes

- `.env`, `docker.env`, local databases, virtual environments, caches, and `node_modules` are ignored.
- Production refuses the default `SECRET_KEY=change-me`.
- Admin login is rate limited.
- Appointment API is rate limited.
- Uploaded post images are validated and rewritten before saving.
- The public site is the Vue frontend; old Flask public templates were removed.
