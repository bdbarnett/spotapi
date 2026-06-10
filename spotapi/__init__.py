from . import objects as _objects
from .auth import (
    AuthorizationCodeAuth,
    ClientCredentialsAuth,
    SpotifyAuthError,
    authorization_url,
    code_challenge_s256,
    generate_code_verifier,
    parse_callback_url,
    pkce_pair,
)
from .client import SpotifyClient, SpotifyClientError, snapshot_id
from .object_specs import SPOTIFY_OBJECT_SPECS
from .objects import (
    Page,
    SpotifyObject,
    get_client,
    make_spotify_class,
    make_spotify_classes,
    set_client,
)
from .scopes import (
    EXAMPLE_SCOPES,
    FOLLOW_WRITE_SCOPES,
    LIBRARY_READ_SCOPES,
    LIBRARY_WRITE_SCOPES,
    PLAYBACK_READ_SCOPES,
    PLAYBACK_WRITE_SCOPES,
    PLAYLIST_READ_SCOPES,
    PLAYLIST_WRITE_SCOPES,
    USER_PROFILE_SCOPES,
)
from .token_cache import TokenCache


for _spec in SPOTIFY_OBJECT_SPECS:
    globals()[_spec["name"]] = getattr(_objects, _spec["name"])


__all__ = (
    "Page",
    "SPOTIFY_OBJECT_SPECS",
    "ClientCredentialsAuth",
    "AuthorizationCodeAuth",
    "SpotifyAuthError",
    "SpotifyClient",
    "SpotifyClientError",
    "SpotifyObject",
    "get_client",
    "make_spotify_class",
    "make_spotify_classes",
    "set_client",
    "snapshot_id",
    "authorization_url",
    "code_challenge_s256",
    "generate_code_verifier",
    "parse_callback_url",
    "pkce_pair",
    "EXAMPLE_SCOPES",
    "FOLLOW_WRITE_SCOPES",
    "LIBRARY_READ_SCOPES",
    "LIBRARY_WRITE_SCOPES",
    "PLAYBACK_READ_SCOPES",
    "PLAYBACK_WRITE_SCOPES",
    "PLAYLIST_READ_SCOPES",
    "PLAYLIST_WRITE_SCOPES",
    "USER_PROFILE_SCOPES",
    "TokenCache",
) + tuple(_spec["name"] for _spec in SPOTIFY_OBJECT_SPECS)


del _objects
del _spec
