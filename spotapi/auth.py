import time

from .transport import query_string, unquote_plus
from .transport import post_form_json


TOKEN_URL = "https://accounts.spotify.com/api/token"
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"


class SpotifyAuthError(Exception):
    pass


class ClientCredentialsAuth:
    def __init__(self, client_id, client_secret, transport=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.transport = transport
        self.access_token = None
        self.expires_at = 0

    def token(self):
        if self.access_token is None or time.time() >= self.expires_at:
            self.refresh()
        return self.access_token

    def refresh(self):
        data = post_form_json(
            TOKEN_URL,
            {"grant_type": "client_credentials"},
            headers={"Authorization": "Basic " + basic_token(self.client_id, self.client_secret)},
            transport=self.transport,
        )

        self.access_token = data["access_token"]
        self.expires_at = time.time() + int(data.get("expires_in", 0)) - 60
        return self.access_token


class AuthorizationCodeAuth:
    def __init__(
        self,
        client_id,
        client_secret,
        redirect_uri,
        scope=None,
        refresh_token=None,
        code_verifier=None,
        transport=None,
        token_cache=None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.refresh_token = refresh_token
        self.code_verifier = code_verifier
        self.transport = transport
        self.token_cache = token_cache
        self.access_token = None
        self.expires_at = 0

        if self.token_cache is not None:
            self.token_cache.load_auth(self)

    def authorize_url(self, state=None, show_dialog=None, code_challenge=None, code_challenge_method=None):
        if code_challenge is None and self.code_verifier is not None:
            code_challenge = code_challenge_s256(self.code_verifier)
            code_challenge_method = "S256"

        return authorization_url(
            self.client_id,
            self.redirect_uri,
            scope=self.scope,
            state=state,
            show_dialog=show_dialog,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )

    def token(self):
        if self.access_token is None or time.time() >= self.expires_at:
            self.refresh()
        return self.access_token

    def exchange_code(self, code):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        if self.code_verifier is not None:
            data["code_verifier"] = self.code_verifier

        return self._update_tokens(self._post_token(data))

    def exchange_callback_url(self, callback_url, expected_state=None):
        values = parse_callback_url(callback_url)
        state = values.get("state")

        if expected_state is not None and state != expected_state:
            raise SpotifyAuthError("OAuth state mismatch")

        error = values.get("error")
        if error is not None:
            raise SpotifyAuthError("OAuth callback error: " + error)

        code = values.get("code")
        if code is None:
            raise SpotifyAuthError("OAuth callback did not include a code")

        return self.exchange_code(code)

    def refresh(self):
        if self.refresh_token is None:
            raise SpotifyAuthError("A refresh_token or authorization code is required")

        return self._update_tokens(
            self._post_token(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                }
            )
        )

    def _post_token(self, data):
        return post_form_json(
            TOKEN_URL,
            data,
            headers={"Authorization": "Basic " + basic_token(self.client_id, self.client_secret)},
            transport=self.transport,
        )

    def _update_tokens(self, data):
        self.access_token = data["access_token"]
        self.expires_at = time.time() + int(data.get("expires_in", 0)) - 60

        if data.get("refresh_token") is not None:
            self.refresh_token = data["refresh_token"]

        if self.token_cache is not None:
            self.token_cache.save_auth(self)

        return self.access_token


def authorization_url(
    client_id,
    redirect_uri,
    scope=None,
    state=None,
    show_dialog=None,
    code_challenge=None,
    code_challenge_method=None,
):
    query = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    add_query(query, "scope", join_scope(scope))
    add_query(query, "state", state)
    add_query(query, "show_dialog", bool_string(show_dialog))
    add_query(query, "code_challenge", code_challenge)
    add_query(query, "code_challenge_method", code_challenge_method)

    return AUTHORIZE_URL + "?" + query_string(query)


def parse_callback_url(callback_url):
    query = callback_url
    question = query.find("?")
    if question >= 0:
        query = query[question + 1:]

    fragment = query.find("#")
    if fragment >= 0:
        query = query[:fragment]

    values = {}
    if not query:
        return values

    for part in query.split("&"):
        if not part:
            continue

        equal = part.find("=")
        if equal < 0:
            key = part
            value = ""
        else:
            key = part[:equal]
            value = part[equal + 1:]

        values[unquote_plus(key)] = unquote_plus(value)

    return values


def generate_code_verifier(length=64):
    if length < 43 or length > 128:
        raise SpotifyAuthError("PKCE code verifier length must be between 43 and 128")

    random_bytes = random_bytes_for_verifier(length)
    verifier = base64_urlsafe(random_bytes)

    if len(verifier) < length:
        return generate_code_verifier(length)

    return verifier[:length]


def code_challenge_s256(code_verifier):
    try:
        import hashlib
    except ImportError:
        raise SpotifyAuthError("hashlib is required for PKCE S256 code challenges")

    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64_urlsafe(digest)


def pkce_pair(length=64):
    verifier = generate_code_verifier(length)
    return verifier, code_challenge_s256(verifier)


def random_bytes_for_verifier(length):
    try:
        import os
        return os.urandom(length)
    except (AttributeError, ImportError):
        try:
            import urandom
            return bytes(urandom.getrandbits(8) for _ in range(length))
        except ImportError:
            raise SpotifyAuthError("A random byte source is required for PKCE code verifier generation")


def base64_urlsafe(data):
    try:
        import base64
    except ImportError:
        raise SpotifyAuthError("base64 is required for PKCE helpers")

    encoded = base64.b64encode(data).decode("ascii")
    encoded = encoded.rstrip("=")
    encoded = encoded.replace("+", "-")
    encoded = encoded.replace("/", "_")
    return encoded


def join_scope(scope):
    if scope is None:
        return None
    if isinstance(scope, str):
        return scope
    return " ".join(scope)


def bool_string(value):
    if value is None:
        return None
    if value:
        return "true"
    return "false"


def add_query(query, key, value):
    if value is not None:
        query[key] = value


def basic_token(client_id, client_secret):
    raw = (client_id + ":" + client_secret).encode("utf-8")

    try:
        import base64
        return base64.b64encode(raw).decode("ascii")
    except ImportError:
        import binascii
        return binascii.b2a_base64(raw).strip().decode("ascii")
