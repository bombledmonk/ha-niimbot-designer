"""Constants for the NIIMBOT Label Designer integration."""

DOMAIN = "niimbot_designer"

# Where the built niimblue fork (and the placeholder page) is served from.
STATIC_URL = "/niimbot_designer_static"
PANEL_URL_PATH = "niimbot-designer"
PANEL_TITLE = "Label Designer"
PANEL_ICON = "mdi:label-outline"

STORAGE_KEY = f"{DOMAIN}.library"
STORAGE_VERSION = 1
SAVE_DELAY = 2

EVENT_PRINTED = f"{DOMAIN}_printed"

# hass-niimbot, which owns the Bluetooth connection.
NIIMBOT_DOMAIN = "niimbot"
NIIMBOT_PRINT = "print"

# Verified on a D110_M: the design (wider than tall) must be turned 90 degrees
# so its short side runs across the print head.
DEFAULT_ROTATE = 90
