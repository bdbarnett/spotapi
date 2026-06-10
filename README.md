# spotapi

Small Spotify Web API client experiments for CPython, MicroPython, and CircuitPython.

The current focus is a lightweight object layer:

- Dict-backed Spotify objects
- Lazy hydration from simplified objects to full objects
- Spec-driven class creation
- Generic page navigation helpers
- Manual bearer token, Client Credentials auth, and Authorization Code auth helpers
- Transport functions isolated in `spotapi.transport`

OAuth Authorization Code helpers include URL generation, callback parsing,
token exchange, refresh handling, PKCE helpers, and CPython local callback
examples.

## Quick Start

```python
from spotapi import SpotifyClient

client = SpotifyClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
)

track = client.track("11dFghVXANMlKmJXsNCbNl", market="US")

print(track.name)
print(track.album.name)
print(track.artists[0].name)
```

## Smoke Test

Set credentials in the environment, then run:

```powershell
$env:SPOTIFY_CLIENT_ID = "your-client-id"
$env:SPOTIFY_CLIENT_SECRET = "your-client-secret"
python scripts\smoke_client_credentials.py
```

Expected output includes a track, album, and artist name.

## Examples

```powershell
python examples\client_credentials_track.py
python examples\page_navigation.py
python examples\custom_transport.py
python examples\authorization_code_url.py
python examples\authorization_code_exchange.py
python examples\authorization_code_pkce_url.py
python examples\authorization_code_pkce_exchange.py
python examples\authorization_code_local_server.py
python examples\authorization_code_pkce_local_server.py
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
python examples\refresh_token_add_to_queue.py
python examples\refresh_token_create_playlist.py
python examples\refresh_token_add_playlist_track.py
python examples\refresh_token_set_playlist_cover.py
python examples\refresh_token_save_track.py
```

The examples read `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from the environment.
`custom_transport.py` shows how CPython `requests`, MicroPython `urequests`, or
CircuitPython `adafruit_requests`-style modules can be adapted.

For Authorization Code auth, run `authorization_code_url.py`, open the printed URL,
then set `SPOTIFY_CALLBACK_URL` to the full redirect URL before running
`authorization_code_exchange.py`. The exchange example prints tokens to the terminal
and does not save them.

The auth URL examples use `EXAMPLE_SCOPES`, which includes the read and guarded
write scopes used by the examples. Set `SPOTIFY_SCOPES` to a space-separated
scope list to request narrower permissions.

After you have a refresh token, set `SPOTIFY_REFRESH_TOKEN` and run
`refresh_token_user_profile.py` to make a user-authenticated API request.

For PKCE, run `authorization_code_pkce_url.py`, keep the printed
`code_verifier`, then set `SPOTIFY_CODE_VERIFIER` before running
`authorization_code_pkce_exchange.py`.

On CPython, `authorization_code_local_server.py` starts a one-request localhost
callback server on `http://127.0.0.1:8080` and exchanges the code for
tokens automatically. `authorization_code_pkce_local_server.py` does the same
with a PKCE verifier and S256 challenge.

The local-server examples save token data to `tokens.json`, which is ignored
by Git. `refresh_token_user_profile.py` reads `SPOTIFY_REFRESH_TOKEN` first, then
falls back to `tokens.json`; `refresh_token_saved_tracks.py` does the same and
demonstrates user-library paging. `refresh_token_playlists.py` lists your
playlists and track totals.

Library code can use `TokenCache("tokens.json")` with `AuthorizationCodeAuth`
to load and save access/refresh token data.

`refresh_token_save_track.py` mutates your library, so it only runs when
`SPOTIFY_RUN_WRITE_EXAMPLE=1` is set. `refresh_token_add_playlist_track.py`
also requires `SPOTIFY_PLAYLIST_ID`; `refresh_token_create_playlist.py`
requires `SPOTIFY_USER_ID`. `refresh_token_set_playlist_cover.py` requires
`SPOTIFY_PLAYLIST_ID` and `SPOTIFY_PLAYLIST_COVER_JPEG`.

## Tests

```powershell
python -m unittest discover -s tests
```

## Packaging

Build local source and wheel distributions with:

```powershell
python -m build
```

The wheel contains only the `spotapi` runtime package. The source distribution
also includes examples, scripts, tests, and project notes. Generated draft specs
and local token files are excluded.

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

- OAuth Authorization Code has URL, code-exchange, refresh-token helpers, and a CPython local callback example.
- User-specific endpoints need a user access token; Client Credentials is not enough.
- The default HTTP transport uses CPython `urllib`.
- MicroPython/CircuitPython users should pass a compatible custom transport.

See `ROADMAP.md` for implemented areas, next steps, and open design questions.
See `PORTABILITY.md` for CPython, MicroPython, and CircuitPython boundary notes.
