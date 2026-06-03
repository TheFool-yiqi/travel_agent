"""密码哈希（bcrypt）。"""

from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    """哈希明文密码，返回可入库的字符串。"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否与哈希一致。"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False
