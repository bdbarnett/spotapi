# spotapi

Small Spotify Web API client experiments for CPython, MicroPython, and CircuitPython.

The current focus is a lightweight object layer:

- Dict-backed Spotify objects
- Lazy hydration from simplified objects to full objects
- Spec-driven class creation
- Generic page navigation helpers
- Manual bearer token, Client Credentials auth, and Authorization Code auth helpers
- Local config file for credentials and example settings
- `user_client()` helper with automatic browser OAuth on first use
- Transport functions isolated in `spotapi.transport`

OAuth Authorization Code helpers include URL generation, callback parsing,
token exchange, refresh handling, PKCE helpers, and CPython interactive login
through `spotapi.oauth_flow`.

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

- `spotapi.local.json` — app credentials and example settings
- `tokens.json` — saved OAuth access/refresh tokens after browser login

## Quick Start

App-authenticated request:

```python
from spotapi import app_client

client = app_client()
track = client.track("11dFghVXANMlKmJXsNCbNl", market="US")

print(track.name)
print(track.album.name)
print(track.artists[0].name)
```

User-authenticated request:

```python
from spotapi import user_client

client = user_client()
user = client.me()

print(user.display_name)
```

On the first call, `user_client()` prints step-by-step browser login
instructions, runs PKCE OAuth on `http://127.0.0.1:8080`, saves tokens to
`tokens.json`, and then continues. Later calls refresh the saved token
automatically.

On WSL, copy the printed authorize URL into a browser on Windows if it does
not open automatically.

You can also construct clients manually:

```python
from spotapi import SpotifyClient

client = SpotifyClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
)
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

Run examples from the project root:

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

User examples call `user_client()` and authenticate automatically when needed.
App examples call `app_client()`.

`custom_transport.py` shows how CPython `requests`, MicroPython `urequests`, or
CircuitPython `adafruit_requests`-style modules can be adapted while still
reading credentials from `spotapi.local.json`.

### Write Examples

Write examples are disabled by default. Enable them in `spotapi.local.json`:

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
python examples\refresh_token_add_to_queue.py
python examples\refresh_token_create_playlist.py
python examples\refresh_token_add_playlist_track.py
python examples\refresh_token_set_playlist_cover.py
python examples\refresh_token_save_track.py
```

Optional config fields also include `playlist_name`, `playlist_description`,
`track_uri`, and `scopes`.

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

For most use, prefer `user_client()` instead of the manual OAuth flow.

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

Compare `SpotifyClient` endpoint coverage to Spotify's OpenAPI paths with:

```powershell
python scripts\endpoint_coverage.py
```

The report lists covered endpoints and the currently missing API paths.

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

Some playback and user methods require a user access token from Authorization Code flow.

## Current Limitations

- Interactive browser OAuth uses CPython `http.server` and `webbrowser`.
- User-specific endpoints need a user access token; Client Credentials is not enough.
- The default HTTP transport uses CPython `urllib`.
- MicroPython/CircuitPython users should pass a compatible custom transport.

See `ROADMAP.md` for implemented areas, next steps, and open design questions.
See `PORTABILITY.md` for CPython, MicroPython, and CircuitPython boundary notes.
