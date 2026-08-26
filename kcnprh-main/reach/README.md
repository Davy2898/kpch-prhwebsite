# Reach (Flask) – Migration of kcnprh

A Flask + PostgreSQL rewrite of the existing PHP news portal.

## Setup
1. Create virtualenv and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2. Environment variables

The project reads `.env` automatically. A prefilled `.env` is included:


3. Database migrations

```bash
flask --app wsgi db init
flask --app wsgi db migrate -m "init"
flask --app wsgi db upgrade
```

4. Run the app

```bash
flask --app wsgi run -p 5001
```

Open http://localhost:5001

## Notes
- Models mirror the existing schema (tables: tbladmin, tblcategory, tblsubcategory, tblposts, tblcomments, tblpages, tblusers).
- Admin login is a placeholder; original passwords were MD5. We will implement secure auth next.
- UI is minimal Jinja now; we’ll port the existing HTML/CSS from `kcnprh/news` incrementally.
