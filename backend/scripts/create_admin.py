"""Create an active user account from explicit CLI arguments."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.repositories.user_repository import UserRepository
from app.db.session import get_session_factory
from app.security import hash_password


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an active Travel Agent user.")
    parser.add_argument("--username", required=True, help="Login username.")
    parser.add_argument("--email", required=True, help="User email.")
    parser.add_argument("--display-name", default=None, help="Optional display name.")
    parser.add_argument(
        "--password",
        default=None,
        help="Plaintext password. Omit to enter it interactively.",
    )
    return parser.parse_args()


async def create_user(args: argparse.Namespace) -> None:
    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    factory = get_session_factory()
    async with factory() as session:
        repo = UserRepository(session)
        if await repo.get_by_username(args.username):
            raise SystemExit(f"Username already exists: {args.username}")
        if await repo.get_by_email(args.email):
            raise SystemExit(f"Email already exists: {args.email}")

        user = await repo.create(
            username=args.username,
            email=args.email,
            display_name=args.display_name,
            password_hash=hash_password(password),
            preferences={},
        )
        await session.commit()
        print(f"Created user {user.username} ({user.id})")


def main() -> None:
    asyncio.run(create_user(parse_args()))


if __name__ == "__main__":
    main()
