import os

from .auth import AuthorizationCodeAuth, SpotifyAuthError
from .client import SpotifyClient
from .token_cache import TokenCache


DEFAULT_REDIRECT_URI = "http://127.0.0.1:8080"
DEFAULT_TOKEN_CACHE_PATH = "tokens.json"


def oauth_credentials_from_env():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SpotifyAuthError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")

    return client_id, client_secret


def redirect_uri_from_env(cached=None, redirect_uri=None):
    if redirect_uri is not None:
        return redirect_uri

    value = os.environ.get("SPOTIFY_REDIRECT_URI")
    if value:
        return value

    if cached is not None and cached.get("redirect_uri"):
        return cached["redirect_uri"]

    return DEFAULT_REDIRECT_URI


def refresh_token_from_env(cached=None):
    value = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    if value:
        return value

    if cached is not None:
        return cached.get("refresh_token")

    return None


def scopes_from_env(cached=None):
    value = os.environ.get("SPOTIFY_SCOPES")
    if value:
        return value.split()

    if cached is not None:
        scope = cached.get("scope")
        if scope:
            if isinstance(scope, str):
                return scope.split()
            return scope

    return None


def token_cache_from_env(token_cache_path=None):
    path = token_cache_path or os.environ.get("SPOTIFY_TOKEN_CACHE", DEFAULT_TOKEN_CACHE_PATH)
    return TokenCache(path)


def authorization_code_auth_from_env(
    token_cache_path=None,
    redirect_uri=None,
    scope=None,
    transport=None,
):
    cache = token_cache_from_env(token_cache_path)
    cached = cache.load()
    client_id, client_secret = oauth_credentials_from_env()
    redirect_uri = redirect_uri_from_env(cached, redirect_uri)
    refresh_token = refresh_token_from_env(cached)

    if not refresh_token:
        raise SpotifyAuthError(
            "Set SPOTIFY_REFRESH_TOKEN or authenticate first to create a token cache"
        )

    if scope is None:
        scope = scopes_from_env(cached)

    return AuthorizationCodeAuth(
        client_id,
        client_secret,
        redirect_uri,
        scope=scope,
        refresh_token=refresh_token,
        token_cache=cache,
        transport=transport,
    )


def user_client_from_env(
    token_cache_path=None,
    redirect_uri=None,
    scope=None,
    transport=None,
    auto_set=True,
):
    auth = authorization_code_auth_from_env(
        token_cache_path=token_cache_path,
        redirect_uri=redirect_uri,
        scope=scope,
        transport=transport,
    )
    return SpotifyClient(auth=auth, transport=transport, auto_set=auto_set)
