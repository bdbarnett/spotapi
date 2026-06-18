# spotify_remote

LVGL touch UI for Spotify playback control, built on [spotapi](../../) and
[lvgl_micropython](https://github.com/lvgl-micropython/lvgl_micropython).

Target display: 1024x600 capacitive touch. Hardware-specific display and input
drivers are intentionally deferred; current development is tested with the
MicroPython Unix port under pydisplay.

## Files

| File | Role |
|------|------|
| `main.py` | Entry point: auth, playback polling, event loop |
| `spotify_ctrl.py` | spotapi wrapper (no LVGL) |
| `ui.py` | LVGL widgets; root screen via `scr = lv.screen_active()` |
| `config.py` | Tunable limits (cover-art cache size, library list size) |
| `artwork_cache.py` | Downloads and caches cover art from Spotify CDN URLs |
| `image_view.py` | Small LVGL cover-art view with a placeholder fallback |
| `genre_seeds.py` | Static genre preset list when the API seed endpoint is unavailable |
| `keyboard_test.py` | pydisplay keyboard smoke test (LVGL textarea input) |

## Prerequisites

- `spotapi` package on `sys.path` (for example `~/.micropython/lib/spotapi` → repo `spotapi/`)
- `spotapi.local.json` and `tokens.json` in **this directory** (see [Config](#config))
- Spotify app scopes: user profile, playback read/write, playlist read/write,
  library read/write, and `user-follow-read` for followed artists
- An active Spotify playback device for now-playing and transport controls
- LVGL image decoder support for the image format returned by Spotify cover art
  URLs. Spotify album art is normally JPEG; the cache also preserves PNG/BMP if
  those formats are encountered.

On startup the app compares required scopes to `tokens.json`. If scopes are
missing, it opens the Spotify authorize URL automatically (same flow as
`spotapi` examples) and saves the updated token. Access tokens are also
refreshed automatically via the refresh token when they expire.

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

Cover art is cached under `art_cache/` beside the app. The cache is gitignored
and reused across app restarts. Limits are set in `config.py`:

- `ART_CACHE_MAX_ITEMS` — max cover-art files on disk (oldest removed first; `0` = unlimited)
- `LIBRARY_LIST_LIMIT` — entries loaded per library category tab
- `BROWSE_LIST_LIMIT` — entries loaded in album and playlist browse views
- `ARTIST_ALBUMS_PAGE_LIMIT` — artist discography page size (Dev Mode max is 10)
- `QUEUE_LIST_LIMIT` — queue rows shown
- `RECENT_LIST_LIMIT` — recently played tracks shown
- `SEARCH_RESULT_LIMIT` — search results (Dev Mode max 10)
- `MAX_ROW_ACTIONS` — action chips per row before overflow

Genre presets load from `GET /recommendations/available-genre-seeds` when the
API allows it; otherwise the app uses the static list in `genre_seeds.py`.

Restart the app after changing `config.py`.

## Linux (MicroPython unix port)

With **pydisplay** on MicroPython unix, `import display_driver` starts the LVGL
event loop via `lv_utils`; importing the app from the REPL returns to `>>>` while
the timer keeps the UI alive. On CircuitPython unix (desktop SDL), apps block in
`display_driver.run()` instead.

```bash
cd /path/to/pydisplay/src
lv -i lib/path.py
>>> from spotify_remote import main
```

For **lvgl_micropython** (without pydisplay), build with SDL display and pointer
input, initialize drivers before importing `ui`, then run with a `TaskHandler`
in scope — see that project's unix example.

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

- **Now** — cover art, track/artist/album metadata, **+PL** / **Like**,
  artist **Albums** / **Follow**, album **Save**, progress slider (drag to seek),
  full-width volume slider, transport (prev, ±15s, play/pause, next),
  shuffle/repeat chips, and status messages
- **Library** (footer) — hub with **Songs**, **Artists**, **Albums**, **Playlists**,
  **Episodes**, **Shows**, and **Audiobooks**;
  row action chips and **Load more** when lists hit the configured limit
- **Queue** — now playing plus upcoming tracks; **Now** plays immediately (remove
  from queue is not supported by Spotify)
- **Recent** — recently played tracks with standard track actions
- **Find** (header) — text search field, type chips (**Tracks**, **Artists**,
  **Albums**, **Playlists**, **Episodes**, **Shows**, **Books**), and a genre
  preset dropdown. Genres load from Spotify's API when permitted; Dev Mode falls
  back to `genre_seeds.py`. Presets use `genre:` filters for tracks and artists.
  Up to 10 results per search in Dev Mode with **Load more**
- **Device picker** — **Refresh**, device type label, and transfer playback

### Row actions (tracks)

Most track lists expose **+Q** (add to queue), **Like**, and **+PL** (add to
owned playlist). Browse views for owned playlists also show **−PL** (remove from
playlist). Album and playlist headers offer **Play**, **Shuffle**, and **Save**
where applicable.

### Navigation

Footer tabs: **Now**, **Library**, **Queue**, **Recent**. Overlay panels (browse,
picker, search, devices) use **Back** to return to the previous screen. The playlist
picker includes **+ New** to create an owned playlist.

Playback state refreshes every 5 seconds and after transport actions. Success
status messages (for example “Queued …”) clear on the next poll.

## Notes

- HTTP calls block briefly; acceptable for v1 bring-up.
- HTTP 429 (rate limit) responses show “Too many requests — wait a moment”.
- Add to Playlist and **−PL** target owned playlists only.
- Spotify's Web API has no remove-from-queue endpoint; the Queue tab offers
  **Now** (play immediately) instead.
- Library save/like uses the unified `/me/library` API (Dev Mode safe).
- Artist **Top Tracks** is not offered (removed); `GET /artists/{id}/top-tracks`
  is unavailable in Spotify Development Mode. Use **Albums** or library browse instead.
- Find supports free-text search via keyboard/textarea and genre presets from the
  dropdown. Returns at most `SEARCH_RESULT_LIMIT` results per request (10 in Dev Mode).
- If LVGL cannot decode a cached image path on the active runtime, list rows
  omit thumbnails rather than failing the screen.
