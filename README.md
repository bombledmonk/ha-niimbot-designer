# NIIMBOT Label Designer for Home Assistant

A sidebar panel for designing NIIMBOT labels in Home Assistant, built on a fork of
[niimblue](https://github.com/bombledmonk/niimblue). Printing goes through
[hass-niimbot](https://github.com/eigger/hass-niimbot), so Home Assistant keeps the
Bluetooth connection and the consumable sensors (labels remaining, battery, …).

## How it works

```
Sidebar panel (niimblue fork, same-origin iframe)
  └─ renders the label to a 1-bit PNG
       └─ websocket: niimbot_designer/print
            └─ niimbot.print with one `dlimg` element (data: URL) → printer over BLE
```

Every print is kept in a label library (`.storage/niimbot_designer.library`): the PNG,
the editor's design JSON, size and settings, and a timestamp per print. Reprint a label
from the panel or with the `niimbot_designer.reprint` action. Each print fires a
`niimbot_designer_printed` event. Marking an entry as saved turns it into a saved design.

## Requirements

- The [NIIMBOT integration](https://github.com/eigger/hass-niimbot) set up with your printer.

## Install (Marketplace, Home Assistant 2026.11+)

1. Settings → Marketplace → **Add from link** → `bombledmonk/ha-niimbot-designer`
   (type **Integration** if asked). The first custom repository asks you to connect
   GitHub with a device code.
2. Open the repository, select **Install**, then restart Home Assistant if a repair asks for it.
3. Settings → Devices & services → Add integration → **NIIMBOT Label Designer**.

On Home Assistant 2026.10 or older, use HACS → ⋮ → Custom repositories instead.

## The editor

The panel is the [niimblue fork](https://github.com/bombledmonk/niimblue/tree/home-assistant)
(`home-assistant` branch), built into `custom_components/niimbot_designer/www/`. Inside
Home Assistant it shows the printer's HA status instead of the Bluetooth connector, prints
through Home Assistant, and adds a library button (history icon) for print history and
saved designs. `www/FRONTEND_COMMIT` records the fork commit; rebuild with
`scripts/update-frontend.ps1`. A plain test page is at `/niimbot_designer_static/test.html`.

Verified on a D110_M with 12 × 40 mm labels: designs are 320 × 96 dots, sent with
a quarter turn. hass-niimbot rotates clockwise, so the editor sends `rotate: 90` for
niimblue's "left" print direction and the left edge prints first. Keep about 1 mm of
margin at the label ends. The first time the editor sees a roll (from hass-niimbot's
label info, e.g. `T12*40`), it sizes the label to match; a size you pick afterwards is kept.

`scripts/ha-ws.ps1` sends one WebSocket command to Home Assistant from a PC, using a
long-lived access token stored DPAPI-encrypted under `%USERPROFILE%\.secrets` (see the
script's header), e.g. `scripts/ha-ws.ps1 -Type niimbot_designer/list -Url https://ha.example.com`.

## WebSocket API

| type | fields | result |
|---|---|---|
| `niimbot_designer/list` | `saved_only?` | `{entries}` (no design JSON) |
| `niimbot_designer/get` | `entry_id` | full entry |
| `niimbot_designer/save` | `entry_id?`, entry fields | `{entry_id}` |
| `niimbot_designer/delete` | `entry_id` | `{deleted}` |
| `niimbot_designer/print` | `entry_id?`, entry fields, `copies?`, `device_id?` | `{entry_id, response}` |

Entry fields: `name`, `saved`, `design`, `png` (`data:image/png;base64,…`), `width`,
`height`, `density`, `label_type`, `rotate`.

## License

MIT
