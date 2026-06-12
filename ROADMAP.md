# spotapi Roadmap

This project currently has a lightweight Spotify Web API object layer, auth helpers,
transport helpers, read methods, selected write methods, examples, and live tests.

## Implemented

- Spec-driven Spotify object classes from `SPOTIFY_OBJECT_SPECS`
- Nested object wrapping for object, object list, typed object, and page fields
- Lazy hydration from simplified objects to full objects (`_get` / `_peek`)
- `Page.__getitem__`, `CursorPaging`, and page-backed `object_by_key` properties
- `Artist.albums` and `Playlist.items` wired to client page methods
- Discovery scripts (`spotapi_*_discovery.py`) for object-graph walkthroughs
- Offline object-layer unit tests in `tests/test_objects.py`
- February 2026 Dev Mode API notes in `PORTABILITY.md`
- `SpotifyObject.__str__()` pretty-prints raw object data for `print()`
- Client Credentials auth
- Authorization Code auth helpers consolidated in `spotapi.auth`
- PKCE verifier/challenge helpers
- `TokenCache` for access/refresh token persistence
- `spotapi.local.json` config file for app credentials
- `examples/write_examples.json` for optional write-example settings
- `SpotifyClient()` config-file bootstrap from `spotapi.local.json`
- Automatic browser OAuth on first `SpotifyClient()` call when needed
- OAuth error translation into `SpotifyAuthError`
- CPython interactive OAuth flow in `spotapi.auth`
- Manual callback URL parsing and lower-level OAuth examples
- Automatic HTTP backend selection (`requests` or CircuitPython `adafruit_requests`)
- JSON and raw-body write transports; non-JSON 2xx responses treated as success
- Read methods for major Spotify object families, paging, search, playback, library, and user endpoints
- Write methods for saved-library items, follows, playlists, and playback controls
- `SnapshotResult` for playlist mutation responses
- Draft schema-to-object-spec generator script
- Endpoint coverage report that parses `spotapi/client.py` and compares it to OpenAPI (`--map` prints path-to-method names)
- First-class client methods for all OpenAPI paths currently reported by Spotify's schema
- Example scripts for client credentials, OAuth, user-library usage, playback controls, and guarded write calls
- Live integration tests against the Spotify Web API

## Good Next Steps

- Add more live tests for read-only user endpoints such as playlists and saved tracks.
- Review MicroPython and CircuitPython compatibility on-device or in their runtimes.
- Keep the schema generator aligned with hand-curated object_by_key overrides and February 2026 endpoint removals.
- Decide whether to package examples, keep them source-only, or move them to docs.
- Retry API requests after token refresh when Spotify returns 401.

## Open Design Questions

- Should `SpotifyClient` stay a singleton-by-default, or should object instances optionally carry a client later?
- Are there additional non-playlist mutation response shapes worth modeling?
- Should write methods validate Spotify limits such as max IDs per request, or leave that to API errors?
- Should config and token files support a configurable base directory for multi-project setups?
