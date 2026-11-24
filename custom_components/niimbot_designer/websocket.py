"""WebSocket API used by the designer panel (auth comes from the HA session)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .library import LabelLibrary
from .printing import async_print_entry

ENTRY_FIELDS = {
    vol.Optional("name"): vol.Any(None, str),
    vol.Optional("saved"): bool,
    vol.Optional("design"): vol.Any(None, dict, list, str),
    vol.Optional("png"): vol.All(str, vol.Match(r"^data:image/png;base64,")),
    vol.Optional("width"): vol.All(int, vol.Range(min=8, max=2000)),
    vol.Optional("height"): vol.All(int, vol.Range(min=8, max=2000)),
    vol.Optional("density"): vol.All(int, vol.Range(min=1, max=20)),
    vol.Optional("label_type"): vol.All(int, vol.Range(min=1, max=11)),
    vol.Optional("rotate"): vol.In([0, 90, 180, 270]),
}


def _library(hass: HomeAssistant) -> LabelLibrary:
    return hass.data[DOMAIN]["library"]


@callback
def async_register(hass: HomeAssistant) -> None:
    for handler in (ws_list, ws_get, ws_save, ws_delete, ws_print):
        websocket_api.async_register_command(hass, handler)


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/list", vol.Optional("saved_only", default=False): bool}
)
@callback
def ws_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], {"entries": _library(hass).list(msg["saved_only"])})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get", vol.Required("entry_id"): str})
@callback
def ws_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _library(hass).get(msg["entry_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "Unknown label")
        return
    connection.send_result(msg["id"], entry)


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/save", vol.Optional("entry_id"): str, **ENTRY_FIELDS}
)
@callback
def ws_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _library(hass).upsert(msg, msg.get("entry_id"))
    connection.send_result(msg["id"], {"entry_id": entry["id"]})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/delete", vol.Required("entry_id"): str})
@callback
def ws_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], {"deleted": _library(hass).delete(msg["entry_id"])})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/print",
        # Either reprint an existing entry, or print a new label (creates an entry).
        vol.Optional("entry_id"): str,
        vol.Optional("copies", default=1): vol.All(int, vol.Range(min=1, max=99)),
        vol.Optional("device_id"): str,
        **ENTRY_FIELDS,
    }
)
@websocket_api.async_response
async def ws_print(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    library = _library(hass)
    entry = library.upsert(msg, msg.get("entry_id"))
    target = {"device_id": msg["device_id"]} if msg.get("device_id") else None
    try:
        result = await async_print_entry(hass, library, entry["id"], msg["copies"], target)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "print_failed", str(err))
        return
    connection.send_result(msg["id"], result)
