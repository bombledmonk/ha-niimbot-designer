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

## Install (HACS)

1. HACS → ⋮ → Custom repositories → add this repo as type **Integration**.
2. Install **NIIMBOT Label Designer** and restart Home Assistant.
3. Settings → Devices & services → Add integration → **NIIMBOT Label Designer**.

## Status

Early scaffold. The panel is a placeholder test page until the niimblue fork is built
into `custom_components/niimbot_designer/www/`.

Verified on a D110_M with 12 × 40 mm labels: designs are 320 × 96 dots, sent with
`rotate: 90`; keep about 1 mm of margin at the label ends.

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
