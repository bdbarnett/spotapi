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
- `spotapi.scopes`
- `spotapi.auth`
- `spotapi.token_cache`

`import spotapi` loads only the portable core plus lazy exports. CPython-only
helpers in `spotapi.config` and `spotapi.oauth_flow` are imported only when
their attributes are accessed, for example `from spotapi import user_client`.

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

## Config And Token Files

`spotapi.config` reads and writes `spotapi.local.json` using `json` and local
file I/O. It is intended for CPython development workflows, examples, scripts,
and live tests.

`spotapi.token_cache` stores OAuth tokens separately in `tokens.json` by default.
Both modules only touch the filesystem when their load/save helpers are called.

On constrained devices, skip these helpers and construct `AuthorizationCodeAuth`
or `SpotifyClient` directly with in-memory tokens.

## Interactive OAuth

`spotapi.oauth_flow` provides the CPython browser login flow used by
`user_client()`. It imports CPython-only modules only when its functions run:

- `http.server` for the localhost callback
- `webbrowser` to open the authorize URL

MicroPython and CircuitPython runtimes should perform OAuth out of band and pass
resulting tokens into `AuthorizationCodeAuth` manually.

## CPython-Only Project Files

The following areas are development or desktop workflows and are not part of the
portable core:

- `scripts/`
- `tests/`
- `spotapi.oauth_flow`
- `spotapi.config`
- examples that load `spotapi.local.json` or call `user_client()`

Portable applications can still use the core client, auth, transport, and object
layers without the config or interactive OAuth helpers.
