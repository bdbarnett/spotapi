# spotapi Roadmap

This project currently has a lightweight Spotify Web API object layer, auth helpers,
transport helpers, read methods, selected write methods, examples, and tests.

## Implemented

- Spec-driven Spotify object classes from `SPOTIFY_OBJECT_SPECS`
- Nested object wrapping for object, object list, typed object, and page fields
- Lazy hydration from simplified objects to full objects
- Client Credentials auth
- Authorization Code auth helpers
- PKCE verifier/challenge helpers
- `TokenCache` for optional access/refresh token persistence
- Manual callback URL parsing and CPython local callback examples
- CPython `urllib` transport plus custom transport hooks
- JSON and raw-body write transports
- Read methods for major Spotify object families, paging, search, playback, library, and user endpoints
- Write methods for saved-library items, follows, playlists, and playback controls
- `SnapshotResult` for playlist mutation responses
- Draft schema-to-object-spec generator script
- Endpoint coverage report script
- First-class client methods for all OpenAPI paths currently reported by Spotify's schema
- Example scripts for client credentials, OAuth, refresh-token usage, and guarded write calls
- Schema coverage tests and endpoint behavior tests

## Good Next Steps

- Add more guarded examples for playback and playlist mutations if they become useful again.
- Run live OAuth smoke tests with a test Spotify account.
- Review MicroPython and CircuitPython compatibility on-device or in their runtimes.
- Improve the schema generator's heuristics for fetch flags and hand-curated field overrides.
- Decide whether to package examples, keep them source-only, or move them to docs.

## Open Design Questions

- Should `SpotifyClient` stay a singleton-by-default, or should object instances optionally carry a client later?
- Are there additional non-playlist mutation response shapes worth modeling?
- Should write methods validate Spotify limits such as max IDs per request, or leave that to API errors?
