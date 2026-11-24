"""NIIMBOT Label Designer: a niimblue-based designer panel that prints through hass-niimbot."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from . import websocket
from .const import DOMAIN, PANEL_ICON, PANEL_TITLE, PANEL_URL_PATH, STATIC_URL
from .library import LabelLibrary
from .printing import async_print_entry

WWW_DIR = Path(__file__).parent / "www"

REPRINT_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Optional("copies", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=99)),
        vol.Optional("device_id"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    library = LabelLibrary(hass)
    await library.async_load()
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data["library"] = library

    # Static paths and WS commands cannot be unregistered; only add them once per run.
    if not domain_data.get("registered"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(WWW_DIR), cache_headers=False)]
        )
        websocket.async_register(hass)
        domain_data["registered"] = True

    # Same-origin iframe: the page reaches the logged-in `hass` object through
    # window.parent, so no tokens are needed.
    frontend.async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL_PATH,
        config={"url": f"{STATIC_URL}/index.html"},
        require_admin=False,
    )

    async def reprint(call: ServiceCall) -> None:
        target = {"device_id": call.data["device_id"]} if call.data.get("device_id") else None
        await async_print_entry(hass, library, call.data["entry_id"], call.data["copies"], target)

    hass.services.async_register(DOMAIN, "reprint", reprint, schema=REPRINT_SCHEMA)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    frontend.async_remove_panel(hass, PANEL_URL_PATH)
    hass.services.async_remove(DOMAIN, "reprint")
    hass.data[DOMAIN].pop("library", None)
    return True
