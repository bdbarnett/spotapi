import contextlib
import os
import sys

from .auth import SpotifyAuthError


def authorize_with_local_server(
    auth,
    redirect_uri,
    state="spotapi",
    message="Spotify authorization received. You can close this window.",
    open_browser=True,
):
    host, port = redirect_uri_host_port(redirect_uri)
    url = auth.authorize_url(state=state, show_dialog=True)

    print_authorize_instructions(url, redirect_uri, open_browser=open_browser)
    callback_url = wait_for_oauth_callback(host, port, message, redirect_uri)
    access_token = auth.exchange_callback_url(callback_url, expected_state=state)

    print()
    print("Authorization complete. Saved tokens for future runs.")
    return access_token


def print_authorize_instructions(url, redirect_uri, open_browser=True):
    print()
    print("=" * 72)
    print("Spotify login required")
    print("=" * 72)
    print()
    print("Complete these steps:")
    print("  1. Open the authorize URL below in your browser.")
    print("  2. Log in to Spotify and approve access.")
    print("  3. Leave this terminal running until the callback is received.")
    print()
    print("Authorize URL:")
    print(url)
    print()

    opened = False
    if open_browser and not running_on_wsl():
        opened = try_open_browser(url)

    if opened:
        print("Opened your browser automatically.")
    elif running_on_wsl():
        print("WSL cannot open a browser automatically.")
        print("Copy the authorize URL above into a browser on Windows.")
    else:
        print("Could not open a browser automatically.")
        print("Copy the authorize URL above into your browser.")

    print()
    print("Waiting for Spotify to redirect to {} ...".format(redirect_uri))
    print()


def try_open_browser(url):
    try:
        import webbrowser
    except ImportError:
        return False

    with suppress_stderr():
        try:
            return webbrowser.open(url)
        except Exception:
            return False


def wait_for_oauth_callback(host, port, message, redirect_uri):
    try:
        from http.server import BaseHTTPRequestHandler, HTTPServer
    except ImportError as error:
        raise SpotifyAuthError(
            "Interactive OAuth requires http.server, which is not available on this runtime"
        ) from error

    class CallbackHandler(BaseHTTPRequestHandler):
        callback_url = None

        def do_GET(self):
            CallbackHandler.callback_url = "http://{}:{}{}".format(host, port, self.path)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(message.encode("utf-8"))

        def log_message(self, format, *args):
            pass

    server = HTTPServer((host, port), CallbackHandler)

    try:
        server.handle_request()
    finally:
        server.server_close()

    if CallbackHandler.callback_url is None:
        raise SpotifyAuthError(
            "No OAuth callback was received at {}. "
            "If the browser could not reach localhost, copy the full redirect URL "
            "into spotapi.local.json as callback_url and run "
            "examples/authorization_code_pkce_exchange.py.".format(redirect_uri)
        )

    return CallbackHandler.callback_url


def running_on_wsl():
    if os.environ.get("WSL_DISTRO_NAME"):
        return True

    try:
        with open("/proc/version") as file:
            return "microsoft" in file.read().lower()
    except OSError:
        return False


@contextlib.contextmanager
def suppress_stderr():
    try:
        devnull = open(os.devnull, "w")
    except OSError:
        yield
        return

    old_stderr = sys.stderr
    sys.stderr = devnull
    try:
        yield
    finally:
        sys.stderr = old_stderr
        devnull.close()


def redirect_uri_host_port(redirect_uri):
    if redirect_uri.startswith("http://"):
        rest = redirect_uri[7:]
        default_port = 80
    elif redirect_uri.startswith("https://"):
        rest = redirect_uri[8:]
        default_port = 443
    else:
        raise SpotifyAuthError("redirect_uri must start with http:// or https://")

    slash = rest.find("/")
    if slash >= 0:
        authority = rest[:slash]
    else:
        authority = rest

    if not authority:
        raise SpotifyAuthError("redirect_uri is missing a host")

    colon = authority.rfind(":")
    if colon >= 0:
        host = authority[:colon]
        port = int(authority[colon + 1:])
    else:
        host = authority
        port = default_port

    return host, port
