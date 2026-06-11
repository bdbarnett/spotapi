# Portability Notes

`spotapi` is intended to keep runtime-specific behavior narrow and easy to
replace.

## Portable Core

These modules should stay free of CPython-only imports at import time and should
run under CPython, MicroPython, and CircuitPython when the runtime has enough
memory:

- `spotapi.objects`
- `spotapi.object_specs`
- `spotapi.client`
- `spotapi.auth`

The client delegates all HTTP behavior to `spotapi.transport`.

## Transport Boundary

`spotapi.transport` owns HTTP and encoding differences:

- CPython default HTTP support through `urllib`
- Custom transport objects/functions for `requests`, `urequests`, or
  `adafruit_requests`
- JSON request/response handling
- Form encoding and URL query encoding
- Raw body uploads
- Response cleanup through `close()` or `deinit()`

MicroPython and CircuitPython users should pass a compatible transport object
instead of relying on the CPython `urllib` fallback.

## Auth

`spotapi.auth` contains OAuth mechanics and uses `spotapi.transport` for network
requests. It imports only lightweight standard modules at import time. PKCE and
Basic auth helpers import optional modules inside helper functions:

- `base64` or `binascii` for Basic auth
- `hashlib` for PKCE S256 challenges
- `os.urandom` or `urandom` for PKCE verifier generation

If a runtime does not provide one of those modules, the relevant helper raises
`SpotifyAuthError`.

`spotapi.auth` also contains:

- `spotapi.local.json` load/save helpers
- `TokenCache` for saving OAuth tokens to `tokens.json`
- Interactive browser OAuth helpers such as `authorize_with_local_server()`

Those helpers import `json`, local file I/O, `http.server`, or `webbrowser` only
when they run. On constrained devices, construct `AuthorizationCodeAuth` or
`SpotifyClient` directly with in-memory tokens instead.

## Config-Based Client

`SpotifyClient()` with no credentials reads `spotapi.local.json`, reuses
`tokens.json` when available, and runs interactive browser OAuth on first use
when needed. That path is intended for CPython development workflows, examples,
scripts, and live tests.

Portable applications can call `SpotifyClient(...)` directly with explicit
credentials, auth, or access tokens instead.

## CPython-Only Workflows

The following areas are development or desktop workflows and are not required on
embedded runtimes:

- `scripts/`
- `tests/`
- examples that load `spotapi.local.json` or call `SpotifyClient()` with no args

Portable applications can still use the core client, auth, transport, and object
layers without the local config file or interactive OAuth helpers.
