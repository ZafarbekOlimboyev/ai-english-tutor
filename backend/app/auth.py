"""Soddalashtirilgan auth — device asosida Bearer token.

Parol yo'q (kirish to'sig'i minimal). Har qurilma ro'yxatdan o'tganда token oladi,
keyingi so'rovlarда `Authorization: Bearer <token>` yuboradi.
"""
import sqlite3

from fastapi import Depends, Header, HTTPException

from app import db


def get_current_user(authorization: str | None = Header(default=None)) -> sqlite3.Row:
    """Authorization sarlavhasidан foydalanuvchини topadi."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token kerak (Authorization: Bearer ...)")

    token = authorization[7:].strip()
    user = db.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Noto'g'ri token")
    return user


CurrentUser = Depends(get_current_user)
