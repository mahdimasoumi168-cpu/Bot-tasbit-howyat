import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
import asyncio

import aiosqlite
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey


class SQLiteFSMStorage(BaseStorage):
    """Persistent FSM storage so form progress survives bot restarts/deploys."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            async with aiosqlite.connect(self.path) as db:
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS fsm_states "
                    "(storage_key TEXT PRIMARY KEY, state TEXT, data TEXT NOT NULL DEFAULT '{}')"
                )
                await db.commit()
            self._initialized = True

    @staticmethod
    def _key(key: StorageKey) -> str:
        return "|".join(str(value or "") for value in (
            key.bot_id, key.chat_id, key.user_id, key.thread_id,
            key.business_connection_id, key.destiny,
        ))

    async def set_state(self, key: StorageKey, state: str | State | None = None) -> None:
        await self._ensure_initialized()
        value = state.state if isinstance(state, State) else state
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO fsm_states(storage_key,state,data) VALUES(?,?, '{}') "
                "ON CONFLICT(storage_key) DO UPDATE SET state=excluded.state",
                (self._key(key), value),
            )
            await db.commit()

    async def get_state(self, key: StorageKey) -> str | None:
        await self._ensure_initialized()
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT state FROM fsm_states WHERE storage_key=?", (self._key(key),)
            ) as cursor:
                row = await cursor.fetchone()
        return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        await self._ensure_initialized()
        payload = json.dumps(dict(data), ensure_ascii=False, default=str)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO fsm_states(storage_key,state,data) VALUES(?,NULL,?) "
                "ON CONFLICT(storage_key) DO UPDATE SET data=excluded.data",
                (self._key(key), payload),
            )
            await db.commit()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        await self._ensure_initialized()
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT data FROM fsm_states WHERE storage_key=?", (self._key(key),)
            ) as cursor:
                row = await cursor.fetchone()
        if not row or not row[0]:
            return {}
        try:
            value = json.loads(row[0])
        except (TypeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    async def close(self) -> None:
        return None
