# spotify_remote

LVGL touch UI for Spotify playback control, built on [spotapi](../../) and
[lvgl_micropython](https://github.com/lvgl-micropython/lvgl_micropython).

Target display: 640×480 capacitive touch (drivers are your responsibility).

## Files

| File | Role |
|------|------|
| `main.py` | Entry point: `TaskHandler` loop, auth, playback polling |
| `spotify_ctrl.py` | spotapi wrapper (no LVGL) |
| `ui.py` | LVGL widgets; root screen via `scr = lv.screen_active()` |

## Prerequisites

- spotapi repo root on `sys.path` (run commands from the repo root)
- `spotapi.local.json` and `tokens.json` from desktop OAuth (see main README)
- Spotify app scopes: user profile, playback read/write, playlist read
- An active Spotify playback device for now-playing and transport controls

## Linux (MicroPython unix port)

Use an lvgl_micropython build with SDL display and pointer input:

```bash
python3 make.py unix DISPLAY=sdl_display INDEV=sdl_pointer
```

Initialize the SDL display **before** importing `ui` or calling `main.py`.
The usual pattern is a small boot script in your lvgl_micropython tree that
creates the bus, display, pointer, and `TaskHandler`, then execs this app.

Minimal flow:

1. Build unix firmware (command above).
2. Copy the `spotapi` package (or repo) where MicroPython can import it.
3. Run from the **spotapi repo root** so `spotapi.local.json` resolves:

```bash
cd /path/to/spotapi
/path/to/lvgl_micropython/build-.../micropython apps/spotify_remote/main.py
```

If `main.py` is launched without a prior display init, `lv.screen_active()` in
`ui.py` will fail. Either prepend your SDL setup to `main.py` or use a wrapper
that inits drivers then runs this module.

`TaskHandler(duration=5)` is recommended for SDL mouse response (see lvgl_micropython unix example).

## Hardware (ESP32 and other MCUs)

1. Flash lvgl_micropython for your board with matching `DISPLAY` and `INDEV`.
2. Copy `spotapi/` and `apps/spotify_remote/` to the device.
3. Copy `spotapi.local.json` and `tokens.json`, or construct auth with an
   in-memory refresh token (no browser OAuth on-device).
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
