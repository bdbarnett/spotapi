from . import objects as _objects
from .auth import (
    AuthorizationCodeAuth,
    ClientCredentialsAuth,
    SpotifyAuthError,
    authorization_url,
    code_challenge_s256,
    generate_code_verifier,
    oauth_error_from_transport,
    parse_callback_url,
    pkce_pair,
    post_oauth_token,
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


_CONFIG_EXPORTS = {
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_REDIRECT_URI",
    "DEFAULT_TOKEN_CACHE_PATH",
    "SpotifyConfigError",
    "app_client",
    "config_available",
    "config_value",
    "credentials_from_config",
    "load_config",
    "redirect_uri_from_config",
    "require_write_examples",
    "save_config",
    "scopes_from_config",
    "token_cache_from_config",
    "user_client",
    "write_examples_enabled",
}


for _spec in SPOTIFY_OBJECT_SPECS:
    globals()[_spec["name"]] = getattr(_objects, _spec["name"])


__all__ = (
    "Page",
    "SPOTIFY_OBJECT_SPECS",
    "ClientCredentialsAuth",
    "AuthorizationCodeAuth",
    "SpotifyAuthError",
    "SpotifyConfigError",
    "SpotifyClient",
    "SpotifyClientError",
    "SpotifyObject",
    "get_client",
    "make_spotify_class",
    "make_spotify_classes",
    "set_client",
    "snapshot_id",
    "authorization_url",
    "authorize_with_local_server",
    "app_client",
    "code_challenge_s256",
    "config_available",
    "config_value",
    "credentials_from_config",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_REDIRECT_URI",
    "DEFAULT_TOKEN_CACHE_PATH",
    "generate_code_verifier",
    "load_config",
    "oauth_error_from_transport",
    "parse_callback_url",
    "pkce_pair",
    "post_oauth_token",
    "redirect_uri_from_config",
    "require_write_examples",
    "save_config",
    "scopes_from_config",
    "token_cache_from_config",
    "user_client",
    "write_examples_enabled",
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


def __getattr__(name):
    if name == "authorize_with_local_server":
        from .oauth_flow import authorize_with_local_server

        return authorize_with_local_server

    if name in _CONFIG_EXPORTS:
        from . import config

        return getattr(config, name)

    raise AttributeError("module {!r} has no attribute {!r}".format(__name__, name))


del _objects
del _spec
