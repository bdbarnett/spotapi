import webbrowser

from http.server import BaseHTTPRequestHandler, HTTPServer
from os import environ

from _bootstrap import bootstrap

bootstrap()

from spotapi import (
    SpotifyAuthError,
    TokenCache,
    redirect_uri_from_env,
    token_cache_from_env,
    user_client_from_env,
)
from spotapi.oauth_env import DEFAULT_TOKEN_CACHE_PATH
from spotapi.scopes import EXAMPLE_SCOPES


HOST = environ.get("SPOTIFY_CALLBACK_HOST", "127.0.0.1")
PORT = int(environ.get("SPOTIFY_CALLBACK_PORT", "8080"))
REDIRECT_URI = environ.get("SPOTIFY_REDIRECT_URI", redirect_uri_from_env())
TOKEN_FILE = environ.get("SPOTIFY_TOKEN_CACHE", DEFAULT_TOKEN_CACHE_PATH)


def open_authorize_url_and_wait(url, message):
    handler = make_callback_handler(message)

    print("Opening:", url)
    webbrowser.open(url)

    server = HTTPServer((HOST, PORT), handler)
    try:
        server.handle_request()
    finally:
        server.server_close()

    if handler.callback_url is None:
        raise SpotifyAuthError("No OAuth callback was received")

    return handler.callback_url


def make_callback_handler(message):
    class CallbackHandler(BaseHTTPRequestHandler):
        callback_url = None

        def do_GET(self):
            CallbackHandler.callback_url = "http://{}:{}{}".format(HOST, PORT, self.path)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(message.encode("utf-8"))

        def log_message(self, format, *args):
            pass

    return CallbackHandler


def print_tokens(auth, access_token):
    print("access_token:", access_token)
    if auth.refresh_token is not None:
        print("refresh_token:", auth.refresh_token)


def save_tokens(auth):
    if auth.refresh_token is None:
        return

    TokenCache(TOKEN_FILE).save_auth(auth)

    print("saved:", TOKEN_FILE)


def load_refresh_token():
    data = load_tokens()
    if data is None:
        return None

    return data.get("refresh_token")


def load_tokens():
    return token_cache_from_env(TOKEN_FILE).load()


def refresh_token_client():
    return user_client_from_env(token_cache_path=TOKEN_FILE, redirect_uri=REDIRECT_URI)


def example_scopes():
    import os

    value = os.environ.get("SPOTIFY_SCOPES")
    if value:
        return value.split()

    return EXAMPLE_SCOPES
