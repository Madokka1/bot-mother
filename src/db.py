from __future__ import annotations

import aiosqlite
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class UserState:
    user_id: int
    tokens: int
    granted_at: Optional[str]


class Database:
    def __init__(self, path: str) -> None:
        self._path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    tokens INTEGER NOT NULL DEFAULT 0,
                    granted_at TEXT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    source_file_id TEXT NULL
                )
                """
            )
            await db.commit()

    async def get_user(self, user_id: int) -> UserState:
        async with aiosqlite.connect(self._path) as db:
            row = await db.execute_fetchone(
                "SELECT user_id, tokens, granted_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            if row:
                return UserState(user_id=row[0], tokens=int(row[1]), granted_at=row[2])

            now = _now_iso()
            await db.execute(
                "INSERT INTO users(user_id, tokens, granted_at, created_at, updated_at) VALUES(?, 0, NULL, ?, ?)",
                (user_id, now, now),
            )
            await db.commit()
            return UserState(user_id=user_id, tokens=0, granted_at=None)

    async def grant_initial_tokens(self, user_id: int, tokens: int = 3) -> UserState:
        async with aiosqlite.connect(self._path) as db:
            row = await db.execute_fetchone(
                "SELECT tokens, granted_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            now = _now_iso()
            if row and row[1]:
                return await self.get_user(user_id)

            if row:
                await db.execute(
                    "UPDATE users SET tokens = ?, granted_at = ?, updated_at = ? WHERE user_id = ?",
                    (int(tokens), now, now, user_id),
                )
            else:
                await db.execute(
                    "INSERT INTO users(user_id, tokens, granted_at, created_at, updated_at) VALUES(?, ?, ?, ?, ?)",
                    (user_id, int(tokens), now, now, now),
                )
            await db.commit()
        return await self.get_user(user_id)

    async def consume_token(self, user_id: int) -> UserState:
        async with aiosqlite.connect(self._path) as db:
            row = await db.execute_fetchone(
                "SELECT tokens FROM users WHERE user_id = ?",
                (user_id,),
            )
            current = int(row[0]) if row else 0
            if current <= 0:
                return await self.get_user(user_id)
            now = _now_iso()
            await db.execute(
                "UPDATE users SET tokens = ?, updated_at = ? WHERE user_id = ?",
                (current - 1, now, user_id),
            )
            await db.commit()
        return await self.get_user(user_id)

    async def add_generation_log(self, user_id: int, prompt: str, source_file_id: str | None) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "INSERT INTO generations(user_id, created_at, prompt, source_file_id) VALUES(?, ?, ?, ?)",
                (user_id, _now_iso(), prompt, source_file_id),
            )
            await db.commit()
