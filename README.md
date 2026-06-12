# spotapi

Small Spotify Web API client experiments for CPython, MicroPython, and CircuitPython.

The current focus is a lightweight object layer:

- Dict-backed Spotify objects
- Lazy hydration from simplified objects to full objects
- Spec-driven class creation
- Generic page navigation helpers
- Manual bearer token, Client Credentials auth, and Authorization Code auth helpers
- Local config files for app credentials and optional write-example settings
- `SpotifyClient()` loads config and runs browser OAuth on first use when needed
- Transport functions isolated in `spotapi.transport`

OAuth Authorization Code helpers include URL generation, callback parsing,
token exchange, refresh handling, PKCE helpers, and CPython interactive login
through `spotapi.auth`.

## Setup

Copy the example config and add your Spotify app credentials:

```powershell
copy spotapi.local.json.example spotapi.local.json
```

Edit `spotapi.local.json`:

```json
{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "redirect_uri": "http://127.0.0.1:8080"
}
```

Register the same `redirect_uri` in your Spotify app dashboard.

Or run the interactive setup script:

```powershell
python scripts\configure.py
```

Local files are ignored by Git:

- `spotapi.local.json` — app credentials
- `tokens.json` — saved OAuth access/refresh tokens after browser login
- `examples/write_examples.json` — settings for write examples (optional)

## Quick Start

```python
from spotapi import SpotifyClient

client = SpotifyClient()
user = client.me()

print(user.display_name)
print(user)
```

`print()` on a Spotify object shows its raw data as formatted JSON. The REPL
still uses the compact `repr`, for example `<PrivateUser id='...'>`.

With `spotapi.local.json` in place, `SpotifyClient()` loads your app
credentials, reuses `tokens.json` when available, and runs PKCE browser login on
first use when needed.

On WSL, copy the printed authorize URL into a browser on Windows if it does
not open automatically.

You can also pass credentials or auth explicitly:

```python
from spotapi import AuthorizationCodeAuth, SpotifyClient

client = SpotifyClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
)

client = SpotifyClient(auth=AuthorizationCodeAuth(...))
client = SpotifyClient(access_token="...")
```

## Smoke Tests

After creating `spotapi.local.json`:

```powershell
python scripts\smoke_client_credentials.py
python scripts\smoke_oauth.py
```

`smoke_client_credentials.py` fetches a public track with Client Credentials.
`smoke_oauth.py` refreshes or acquires a user token, then calls `/me`.

## Examples

Run examples from the project root. Most call `SpotifyClient()` and
authenticate automatically when needed.

### Read Examples

```powershell
python examples\client_credentials_track.py
python examples\page_navigation.py
python examples\custom_transport.py
python examples\refresh_token_user_profile.py
python examples\refresh_token_currently_playing.py
python examples\refresh_token_devices.py
python examples\refresh_token_queue.py
python examples\refresh_token_recently_played.py
python examples\refresh_token_top_artists.py
python examples\refresh_token_top_tracks.py
python examples\refresh_token_playlists.py
python examples\refresh_token_saved_albums.py
python examples\refresh_token_saved_tracks.py
```

`custom_transport.py` fetches available markets with Client Credentials. HTTP is
chosen automatically in `spotapi.transport` from `requests` or a CircuitPython
`adafruit_requests` session.

### Playback Controls

`refresh_token_playback_controls.py` is an interactive terminal demo. It prints
a key map, then loops on single keystrokes to call playback methods such as
`play()`, `pause()`, `next_track()`, `seek()`, `volume()`, and `queue()`, plus
parameterless read methods such as `me()`, `saved_tracks()`, and
`recently_played()`. Press `l` to reprint the key list. Press `Q` to exit.
Requires Premium and an active Spotify device for playback controls. Uses raw
terminal input (`termios`) and is intended for Linux/WSL/macOS terminals.

```powershell
python examples\refresh_token_playback_controls.py
```

Many API paths use descriptive method names rather than URL paths. For example,
`GET /me/tracks` is `saved_tracks()`, not `me_tracks()`. See
[Endpoint Coverage](#endpoint-coverage) to look up path-to-method mappings.

### Write Examples

Copy `examples/write_examples.json.example` to `examples/write_examples.json`.
Write examples are disabled by default. Enable them there:

```json
{
  "allow_write_examples": true,
  "playlist_id": "your-playlist-id",
  "user_id": "your-spotify-user-id",
  "playlist_cover_jpeg": "C:\\path\\to\\cover.jpg"
}
```

Then run:

```powershell
python examples\write_refresh_token_add_to_queue.py
python examples\write_refresh_token_create_playlist.py
python examples\write_refresh_token_add_playlist_track.py
python examples\write_refresh_token_set_playlist_cover.py
python examples\write_refresh_token_save_track.py
```

Optional fields in `examples/write_examples.json` include `playlist_name`,
`playlist_description`, and `track_uri`.

### Manual OAuth Examples

These examples demonstrate lower-level OAuth steps using values from
`spotapi.local.json`:

```powershell
python examples\authorization_code_url.py
python examples\authorization_code_exchange.py
python examples\authorization_code_pkce_url.py
python examples\authorization_code_pkce_exchange.py
python examples\authorization_code_local_server.py
python examples\authorization_code_pkce_local_server.py
```

For the manual exchange examples, add temporary fields to
`spotapi.local.json`:

```json
{
  "callback_url": "http://127.0.0.1:8080/?code=...&state=...",
  "code_verifier": "...",
  "auth_state": "spotapi-pkce-example"
}
```

For most use, prefer `SpotifyClient()` instead of the manual OAuth flow.

Library code can also use `TokenCache("tokens.json")` with
`AuthorizationCodeAuth` to load and save access/refresh token data directly.

## Tests

Tests are live integration tests against the Spotify Web API. Create
`spotapi.local.json` first, then run:

```powershell
python -m unittest discover -s tests -v
```

If the config file is missing, the tests are skipped.

## Packaging

Build local source and wheel distributions with:

```powershell
python -m build
```

The wheel contains only the `spotapi` runtime package. The source distribution
also includes examples, scripts, tests, and project notes. Generated draft specs
and local config/token files are excluded.

## Schema Draft Generation

`object_specs.py` is curated by hand, but a draft can be generated from Spotify's
OpenAPI schema for comparison:

```powershell
python scripts\generate_object_specs.py
```

The default output is `generated_object_specs.py`, which is ignored by Git and
kept outside the import package. YAML schemas require optional `PyYAML`; JSON
OpenAPI schemas work with the standard library.

## Endpoint Coverage

Compare `SpotifyClient` to Spotify's OpenAPI paths by parsing `spotapi/client.py`:

```powershell
python scripts\endpoint_coverage.py
python scripts\endpoint_coverage.py --map
```

The report lists endpoints missing from the client, client-only paths, and (with
`--map`) each OpenAPI path with the matching `SpotifyClient` method names. For
example, `GET /me/tracks` maps to `saved_tracks()`, not a method named after
the URL path.

## Implemented Client Areas

The client currently includes object-returning methods for:

- Single and bulk tracks, albums, artists, episodes, shows, audiobooks, and chapters
- Album tracks, artist albums, artist top tracks, related artists, playlist items/tracks, show episodes, and audiobook chapters
- Audio features, audio analysis, recommendations, search, categories, category playlists, featured playlists, and new releases
- Current playback, currently playing, queue, devices, recently played, current user, public users, and user playlists
- Saved albums, tracks, episodes, shows, audiobooks, followed artists, top artists/tracks, markets, and recommendation genres
- Saved-library membership checks, generic library URI methods, and following checks
- Save/remove saved-library items and follow/unfollow artists/users
- Create/update/follow/unfollow playlists, add/remove/replace/reorder playlist items/tracks, check playlist followers, and upload custom cover images
- `snapshot_id(result)` helper for playlist mutation responses
- Playback controls including transfer, play/pause, skip, seek, repeat, shuffle, volume, and queue add
- Write helpers accept strings or Spotify objects with matching `id`/`uri` fields where appropriate
- Generic `next_page(page)` and `previous_page(page)` navigation for Spotify paging URLs
- First-class methods for all OpenAPI paths currently reported by Spotify's schema
- Low-level HTTP helpers on `SpotifyClient` are private; the public surface is endpoint methods such as `track()`, `pause()`, and `saved_tracks()`

Some playback and user methods require a user access token from Authorization Code flow.
Some playback controls require Spotify Premium and an active device.

## Current Limitations

- Interactive browser OAuth uses CPython `http.server` and `webbrowser`.
- User-specific endpoints need a user access token; Client Credentials is not enough.
- HTTP requires `requests` on CPython and MicroPython, or a CircuitPython
  `adafruit_requests` session.

See `ROADMAP.md` for implemented areas, next steps, and open design questions.
See `PORTABILITY.md` for CPython, MicroPython, and CircuitPython boundary notes.
