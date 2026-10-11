"""Custom ``flask`` command line tasks.

Available after ``set FLASK_APP=run.py`` (or by running ``python -m flask``):

* ``flask init-db``      - create every table from the models
* ``flask seed-data``    - load the repeatable prototype seed data
* ``flask create-admin`` - create or update an administrator account
* ``flask reset-db``     - drop and recreate every table (asks for confirmation)
"""
from __future__ import annotations

import click
from flask import Flask

from app.extensions import db
from app.models import User
from app.seed_data import seed_all


def register(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db() -> None:
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-data")
    @click.option("--with-admin", is_flag=True, help="Also create/refresh the administrator account.")
    def seed_data(with_admin: bool) -> None:
        """Load the repeatable prototype seed data."""
        db.create_all()
        summary = seed_all(
            with_admin=with_admin,
            admin_email=app.config.get("ADMIN_EMAIL", ""),
            admin_password=app.config.get("ADMIN_PASSWORD", ""),
        )
        click.echo("Seed complete:")
        for key, value in summary.items():
            click.echo(f"  {key}: {value}")
        if with_admin and not summary.get("admin"):
            click.echo(
                "  ! No administrator created: set ADMIN_EMAIL and ADMIN_PASSWORD in .env "
                "or run `flask create-admin`.",
                err=True,
            )

    @app.cli.command("create-admin")
    @click.option("--email", prompt="Admin email")
    @click.option("--name", default="Site Administrator", prompt="Display name")
    @click.option(
        "--password",
        prompt="Password",
        hide_input=True,
        confirmation_prompt=True,
        help="The password is hashed before it is stored.",
    )
    def create_admin(email: str, name: str, password: str) -> None:
        """Create or update an administrator account."""
        if len(password) < 8:
            raise click.ClickException("Use a password with at least 8 characters.")
        user = User.query.filter_by(email=email.lower()).first()
        if user is None:
            user = User(name=name, email=email.lower(), role="admin")
            db.session.add(user)
        else:
            user.name = name
            user.role = "admin"
        user.set_password(password)
        db.session.commit()
        click.echo(f"Administrator ready: {user.email}")

    @app.cli.command("reset-db")
    @click.option("--yes", is_flag=True, help="Skip the confirmation prompt (used in automated checks).")
    def reset_db(yes: bool) -> None:
        """Drop every table and recreate an empty database."""
        if not yes:
            click.confirm("This deletes ALL data in the configured database. Continue?", abort=True)
        db.drop_all()
        db.create_all()
        click.echo("Database reset complete.")