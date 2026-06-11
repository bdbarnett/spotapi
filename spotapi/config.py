from .auth import AuthorizationCodeAuth, SpotifyAuthError, generate_code_verifier
from .client import SpotifyClient
from .scopes import EXAMPLE_SCOPES
from .token_cache import TokenCache


DEFAULT_CONFIG_PATH = "spotapi.local.json"
DEFAULT_TOKEN_CACHE_PATH = "tokens.json"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8080"


class SpotifyConfigError(SpotifyAuthError):
    pass


def load_config(path=None):
    config_path = path or DEFAULT_CONFIG_PATH

    try:
        import json
    except ImportError:
        raise SpotifyConfigError("json is required to load spotapi.local.json")

    try:
        with open(config_path) as file:
            data = json.load(file)
    except OSError as error:
        raise SpotifyConfigError(
            "Create {} from spotapi.local.json.example and add your Spotify app credentials".format(
                config_path
            )
        ) from error

    if not isinstance(data, dict):
        raise SpotifyConfigError("{} must contain a JSON object".format(config_path))

    return data


def save_config(data, path=None):
    config_path = path or DEFAULT_CONFIG_PATH

    try:
        import json
    except ImportError:
        return False

    with open(config_path, "w") as file:
        json.dump(data, file, indent=2)
        file.write("\n")

    return True


def config_available(path=None):
    try:
        config = load_config(path)
    except SpotifyConfigError:
        return False

    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    return bool(client_id and client_secret)


def credentials_from_config(config):
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")

    if not client_id or not client_secret:
        raise SpotifyConfigError(
            "spotapi.local.json must include client_id and client_secret"
        )

    return client_id, client_secret


def redirect_uri_from_config(config, cached=None):
    value = config.get("redirect_uri")
    if value:
        return value

    if cached is not None and cached.get("redirect_uri"):
        return cached["redirect_uri"]

    return DEFAULT_REDIRECT_URI


def scopes_from_config(config, cached=None):
    value = config.get("scopes")
    if value:
        if isinstance(value, str):
            return value.split()
        return list(value)

    if cached is not None:
        scope = cached.get("scope")
        if scope:
            if isinstance(scope, str):
                return scope.split()
            return list(scope)

    return list(EXAMPLE_SCOPES)


def token_cache_from_config(config):
    path = config.get("token_cache", DEFAULT_TOKEN_CACHE_PATH)
    return TokenCache(path)


def write_examples_enabled(config=None, path=None):
    if config is None:
        config = load_config(path)
    return bool(config.get("allow_write_examples"))


def require_write_examples(config=None, path=None):
    if config is None:
        config = load_config(path)

    if not write_examples_enabled(config):
        raise SpotifyConfigError(
            "Set allow_write_examples to true in spotapi.local.json to run write examples"
        )


def config_value(config, key, default=None):
    value = config.get(key)
    if value is None:
        return default
    return value


def app_client(config_path=None, transport=None, auto_set=True):
    config = load_config(config_path)
    client_id, client_secret = credentials_from_config(config)

    return SpotifyClient(
        client_id=client_id,
        client_secret=client_secret,
        transport=transport,
        auto_set=auto_set,
    )


def user_client(
    config_path=None,
    scope=None,
    transport=None,
    auto_set=True,
    authenticate_if_needed=True,
    auth_state="spotapi",
):
    config = load_config(config_path)
    client_id, client_secret = credentials_from_config(config)
    cache = token_cache_from_config(config)
    cached = cache.load()
    redirect_uri = redirect_uri_from_config(config, cached)
    refresh_token = cached.get("refresh_token")

    if scope is None:
        scope = scopes_from_config(config, cached)

    if refresh_token:
        auth = AuthorizationCodeAuth(
            client_id,
            client_secret,
            redirect_uri,
            scope=scope,
            refresh_token=refresh_token,
            token_cache=cache,
            transport=transport,
        )
        return SpotifyClient(auth=auth, transport=transport, auto_set=auto_set)

    if not authenticate_if_needed:
        raise SpotifyConfigError(
            "No refresh token in {}. Run an example to authenticate in the browser first.".format(
                cache.path
            )
        )

    code_verifier = generate_code_verifier()
    auth = AuthorizationCodeAuth(
        client_id,
        client_secret,
        redirect_uri,
        scope=scope,
        code_verifier=code_verifier,
        token_cache=cache,
        transport=transport,
    )
    from .oauth_flow import authorize_with_local_server

    authorize_with_local_server(
        auth,
        redirect_uri=redirect_uri,
        state=auth_state,
        message="Spotify authorization received. You can close this window.",
    )
    return SpotifyClient(auth=auth, transport=transport, auto_set=auto_set)
