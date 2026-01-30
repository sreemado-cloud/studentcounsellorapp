"""
JWT revocation via token sessions (allowlist).
- On login: add session (jti, user_id, exp).
- On get_current_user: check session exists; else 401.
- On logout: delete session by jti.
- On password change / set-password / deactivate: delete all sessions for user.
"""
from datetime import datetime

from app.core.database import get_database


async def add_session(jti: str, user_id: str, exp: datetime) -> None:
    """Record an active token session (uses same DB as rest of app)."""
    db = await get_database()
    await db.token_sessions.insert_one({
        "jti": jti,
        "user_id": user_id,
        "exp": exp,
    })


async def delete_session(jti: str) -> None:
    """Revoke a single token by jti."""
    db = await get_database()
    await db.token_sessions.delete_one({"jti": jti})


async def delete_sessions_for_user(user_id: str) -> None:
    """Revoke all tokens for a user (e.g. password change, deactivate)."""
    db = await get_database()
    await db.token_sessions.delete_many({"user_id": user_id})


async def session_exists(jti: str) -> bool:
    """Return True if this token session is still valid."""
    db = await get_database()
    doc = await db.token_sessions.find_one({"jti": jti})
    return doc is not None
