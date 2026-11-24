"""Send a library entry to hass-niimbot, which owns the Bluetooth link."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_ROTATE, EVENT_PRINTED, NIIMBOT_DOMAIN, NIIMBOT_PRINT
from .library import LabelLibrary


def build_print_data(entry: dict[str, Any], copies: int, preview: bool = False) -> dict[str, Any]:
    """niimbot.print data: the finished 1-bit PNG as a single dlimg element."""
    width, height = int(entry["width"]), int(entry["height"])
    data: dict[str, Any] = {
        "width": width,
        "height": height,
        "rotate": int(entry.get("rotate", DEFAULT_ROTATE)),
        "copies": copies,
        "payload": [
            {
                "type": "dlimg",
                "x": 0,
                "y": 0,
                "xsize": width,
                "ysize": height,
                "url": entry["png"],
            }
        ],
    }
    if entry.get("density"):
        data["density"] = int(entry["density"])
    if entry.get("label_type"):
        data["label_type"] = int(entry["label_type"])
    if preview:
        data["preview"] = True
    return data


async def async_print_entry(
    hass: HomeAssistant,
    library: LabelLibrary,
    entry_id: str,
    copies: int = 1,
    target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Print an entry, record the outcome in its history and fire an event."""
    entry = library.get(entry_id)
    if entry is None:
        raise HomeAssistantError(f"Unknown label {entry_id}")
    if not entry.get("png"):
        raise HomeAssistantError("Label has no rendered image to print")

    ok, error, response = True, None, None
    try:
        response = await hass.services.async_call(
            NIIMBOT_DOMAIN,
            NIIMBOT_PRINT,
            build_print_data(entry, copies),
            target=target,
            blocking=True,
            return_response=True,
        )
    except Exception as err:  # noqa: BLE001 - surface any print failure to the user
        ok, error = False, str(err)

    library.record_print(entry_id, copies, ok, error)
    hass.bus.async_fire(
        EVENT_PRINTED,
        {"entry_id": entry_id, "name": entry.get("name"), "copies": copies, "ok": ok, "error": error},
    )
    if not ok:
        raise HomeAssistantError(f"Print failed: {error}")
    return {"entry_id": entry_id, "response": response}
