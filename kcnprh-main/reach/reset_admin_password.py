from datetime import UTC, datetime
import secrets
import string
import sys

from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app import create_app
from app import db
from app.models import Admin


def make_password() -> str:
    chars = string.ascii_letters + string.digits
    return "Kcnprh@" + "".join(secrets.choice(chars) for _ in range(10))


app = create_app()


with app.app_context():
    if str(db.engine.url).startswith("sqlite:"):
        db.create_all()

    password = sys.argv[1] if len(sys.argv) > 1 else make_password()
    admin = Admin.query.filter_by(AdminUserName="admin").first()
    created = admin is None

    if admin is None:
        next_id = (db.session.query(func.max(Admin.id)).scalar() or 0) + 1
        admin = Admin(
            id=next_id,
            AdminUserName="admin",
            AdminEmailId="admin@kcnprh.local",
            userType=1,
            CreationDate=datetime.now(UTC),
        )
        db.session.add(admin)

    admin.AdminPassword = generate_password_hash(password)
    admin.UpdationDate = datetime.now(UTC)
    db.session.commit()

    print("created admin" if created else "updated admin")
    print("username=admin")
    print(f"password={password}")
