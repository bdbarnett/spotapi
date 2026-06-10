# Portability Notes

`spotapi` is intended to keep runtime-specific behavior narrow and easy to
replace.

## Portable Core

These modules should stay free of CPython-only imports and should run under
CPython, MicroPython, and CircuitPython when the runtime has enough memory:

- `spotapi.objects`
- `spotapi.object_specs`
- `spotapi.client`
- `spotapi.scopes`

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

## Token Cache

`spotapi.token_cache` is optional. It uses `json` and local file I/O only when
`load()` or `save()` is called. Applications on constrained devices can skip it
or provide their own cache object with `load_auth(auth)` and `save_auth(auth)`.

## CPython-Only Project Files

The following areas are development or desktop examples and are not part of the
portable core:

- `scripts/`
- `tests/`
- local OAuth server examples using `http.server` and `webbrowser`
- examples that read environment variables with `os.environ`

