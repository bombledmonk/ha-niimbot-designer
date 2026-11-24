"""Label library: every printed label (history) and every saved design.

One store holds both. A print creates an entry (or adds a timestamp to an
existing one on reprint); "saving" a design just sets ``saved`` on an entry,
printed or not.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import SAVE_DELAY, STORAGE_KEY, STORAGE_VERSION

# Fields a client may set on an entry.
EDITABLE = ("name", "saved", "design", "png", "width", "height", "density", "label_type", "rotate")


class LabelLibrary:
    """Persisted list of label entries, newest first."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._entries: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self._entries = {e["id"]: e for e in data.get("entries", [])}

    def _schedule_save(self) -> None:
        self._store.async_delay_save(
            lambda: {"entries": list(self._entries.values())}, SAVE_DELAY
        )

    def list(self, saved_only: bool = False) -> list[dict[str, Any]]:
        """Summaries (no design JSON), newest activity first."""
        entries = [e for e in self._entries.values() if e.get("saved") or not saved_only]
        entries.sort(key=lambda e: e.get("updated", ""), reverse=True)
        return [{k: v for k, v in e.items() if k != "design"} for e in entries]

    def get(self, entry_id: str) -> dict[str, Any] | None:
        return self._entries.get(entry_id)

    def upsert(self, fields: dict[str, Any], entry_id: str | None = None) -> dict[str, Any]:
        now = dt_util.utcnow().isoformat()
        entry = self._entries.get(entry_id) if entry_id else None
        if entry is None:
            entry = {
                "id": uuid4().hex,
                "created": now,
                "name": None,
                "saved": False,
                "prints": [],
            }
            self._entries[entry["id"]] = entry
        entry.update({k: v for k, v in fields.items() if k in EDITABLE})
        entry["updated"] = now
        self._schedule_save()
        return entry

    def record_print(self, entry_id: str, copies: int, ok: bool, error: str | None) -> dict[str, Any]:
        entry = self._entries[entry_id]
        now = dt_util.utcnow().isoformat()
        entry["prints"].append({"at": now, "copies": copies, "ok": ok, "error": error})
        entry["updated"] = now
        self._schedule_save()
        return entry

    def delete(self, entry_id: str) -> bool:
        if self._entries.pop(entry_id, None) is None:
            return False
        self._schedule_save()
        return True
