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

    if open_browser:
        try:
            import webbrowser
        except ImportError:
            print("Open this URL in your browser:", url)
        else:
            print("Opening:", url)
            webbrowser.open(url)
    else:
        print("Open this URL in your browser:", url)

    callback_url = wait_for_oauth_callback(host, port, message)
    return auth.exchange_callback_url(callback_url, expected_state=state)


def wait_for_oauth_callback(host, port, message):
    try:
        from http.server import BaseHTTPRequestHandler, HTTPServer
    except ImportError as error:
        raise SpotifyAuthError(
            "Interactive OAuth requires http.server, which is not available on this runtime"
        ) from error

    handler = _callback_handler(host, port, message)
    server = HTTPServer((host, port), handler)

    try:
        server.handle_request()
    finally:
        server.server_close()

    if handler.callback_url is None:
        raise SpotifyAuthError("No OAuth callback was received")

    return handler.callback_url


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


def _callback_handler(host, port, message):
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

    return CallbackHandler
