from flask import Flask
from flask.cli import FlaskGroup
from app import create_app, db

app: Flask = create_app()
cli = FlaskGroup(create_app=create_app)

@cli.command("create_db")
def create_db():
    """Create database tables."""
    db.create_all()
    print("Database tables created")

if __name__ == "__main__":
    cli()
