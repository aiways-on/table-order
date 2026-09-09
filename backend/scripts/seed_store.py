"""Seed (or update) a store + admin account so you can log in.

There is no public sign-up endpoint — a store row must exist before admin
login works. Run this once against the running DB.

Usage (inside the backend container or a venv with deps + .env loaded):

    python -m scripts.seed_store \
        --store-code cafe1 --name "데모 카페" \
        --admin owner --password changeme123

Defaults create: store_code=cafe1, admin=owner, password=changeme123.
Re-running with the same --store-code updates the name/username/password
(idempotent).
"""
from __future__ import annotations

import argparse

from sqlalchemy import select

from app.auth.security import hash_password
from app.core.database import SessionLocal
from app.shared.models import Store


def main() -> None:
    p = argparse.ArgumentParser(description="Seed a store + admin account.")
    p.add_argument("--store-code", default="cafe1")
    p.add_argument("--name", default="데모 카페")
    p.add_argument("--admin", default="owner")
    p.add_argument("--password", default="changeme123")
    args = p.parse_args()

    if len(args.password) < 8:
        p.error("--password must be at least 8 characters (matches login validation).")

    db = SessionLocal()
    try:
        store = db.execute(
            select(Store).where(Store.store_code == args.store_code)
        ).scalar_one_or_none()
        if store is None:
            store = Store(
                store_code=args.store_code,
                name=args.name,
                admin_username=args.admin,
                admin_password_hash=hash_password(args.password),
            )
            db.add(store)
            action = "created"
        else:
            store.name = args.name
            store.admin_username = args.admin
            store.admin_password_hash = hash_password(args.password)
            action = "updated"
        db.commit()
        db.refresh(store)
        print(f"Store {action}: id={store.id}")
        print(f"  store_code     = {args.store_code}")
        print(f"  admin_username = {args.admin}")
        print(f"  password       = {args.password}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
