# spotify_remote

LVGL touch UI for Spotify playback control, built on [spotapi](../../) and
[lvgl_micropython](https://github.com/lvgl-micropython/lvgl_micropython).

Target display: 640×480 capacitive touch (drivers are your responsibility).

## Files

| File | Role |
|------|------|
| `main.py` | Entry point: auth, playback polling, event loop |
| `spotify_ctrl.py` | spotapi wrapper (no LVGL) |
| `ui.py` | LVGL widgets; root screen via `scr = lv.screen_active()` |

## Prerequisites

- `spotapi` package on `sys.path` (for example `~/.micropython/lib/spotapi` → repo `spotapi/`)
- `spotapi.local.json` and `tokens.json` in **this directory** (see [Config](#config))
- Spotify app scopes: user profile, playback read/write, playlist read
- An active Spotify playback device for now-playing and transport controls

## Config

`spotify_ctrl.py` loads credentials from this app directory (via `__file__`), not
from the process cwd. Copy or symlink secrets here:

```bash
cd apps/spotify_remote
cp ../../spotapi.local.json.example spotapi.local.json
# edit spotapi.local.json, run desktop OAuth once, then copy or link tokens.json
ln -s ../../tokens.json tokens.json   # optional: reuse repo-root tokens
```

Both files are gitignored. When this folder is symlinked elsewhere (for example
`pydisplay/src/examples/spotify_remote`), paths still resolve to the real app
directory.

## Linux (MicroPython unix port)

With **pydisplay**, `import display_driver` starts the LVGL event loop via
`lv_utils`; no `TaskHandler` or blocking refresh loop is required on Linux.
Import the app from the REPL after display init:

```bash
cd /path/to/pydisplay/src
lv -i lib/path.py
>>> from spotify_remote import main
```

For **lvgl_micropython** (without pydisplay), build with SDL display and pointer
input, initialize drivers before importing `ui`, then run with a `TaskHandler`
(`th`) in scope — see that project's unix example.

## Hardware (ESP32 and other MCUs)

1. Flash lvgl_micropython for your board with matching `DISPLAY` and `INDEV`.
2. Copy `spotapi/` and this app to the device.
3. Place `spotapi.local.json` and `tokens.json` in this app directory, or
   construct auth with an in-memory refresh token (no browser OAuth on-device).
4. In `main.py`, replace the driver comment block with your display/touch init
   (bus, frame buffers, `display.init()`, touch `indev`, backlight, rotation).
5. Run `main.py` on boot or from the REPL.

Display init must complete before `SpotifyUI` is created.

## UI overview

- **Now** — track, artist, progress bar, prev / play-pause / next
- **Lists** — owned playlists only (Dev Mode); tap to play playlist context

Playback state refreshes every 3 seconds and after transport actions.

## Notes

- HTTP calls block briefly; acceptable for v1 bring-up.
- Followed playlists are excluded (same constraint as `spotapi_playlist_discovery.py`).
- Album art and device picker are not implemented yet.
