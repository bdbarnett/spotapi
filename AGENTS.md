# AGENTS.md

## Cursor Cloud specific instructions

`spotapi` is a single, pure-Python (stdlib-only) Spotify Web API **client library**
targeting CPython/MicroPython/CircuitPython. There are no servers, databases, or
background services to run — it is a library plus `tests/`, `examples/`, and `scripts/`.

The startup update script installs the package editable into the system Python with
`pip install --break-system-packages -e ".[schema]"` plus `build`. (`--break-system-packages`
is used because the VM's Ubuntu system Python is PEP-668 "externally managed"; a venv
would otherwise require the `python3.12-venv` system package, which is not part of the
codebase.) Use `python3` (there is no `python` alias on the VM).

Common commands (run from repo root):
- Tests (offline, no creds/network): `python3 -m unittest discover -s tests` — see `README.md` "Tests".
- Build (packaging = the library "build"): `python3 -m build` — see `README.md` "Packaging".
- Lint: none configured (no ruff/mypy/flake8 config exists despite cache entries in `.gitignore`).

Non-obvious notes:
- The full test suite runs entirely offline with mocked transports; no Spotify
  credentials or network are required for tests/build.
- `examples/*.py` and `scripts/smoke_client_credentials.py` need real Spotify
  credentials (`SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`, and a refresh token /
  callback URL for user-scoped flows) and live network. They are NOT needed to
  verify the environment.
- `scripts/endpoint_coverage.py` and `scripts/generate_object_specs.py` fetch
  Spotify's OpenAPI schema from the network by default (pass a local schema path to
  run offline); `generate_object_specs.py` only needs `PyYAML` (the `schema` extra)
  for YAML schemas.
- To exercise the client without network, inject a custom transport object exposing
  `get`/`post` (requests-style) into `SpotifyClient(..., transport=...)`; see
  `examples/custom_transport.py` and `tests/test_client.py` for the pattern.
