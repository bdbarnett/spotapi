import os

from _bootstrap import bootstrap

bootstrap()

from spotapi import AuthorizationCodeAuth


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080")
    callback_url = os.environ.get("SPOTIFY_CALLBACK_URL")
    code_verifier = os.environ.get("SPOTIFY_CODE_VERIFIER")
    expected_state = os.environ.get("SPOTIFY_AUTH_STATE")

    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
    if not callback_url:
        raise SystemExit("Set SPOTIFY_CALLBACK_URL to the full URL Spotify redirected to")
    if not code_verifier:
        raise SystemExit("Set SPOTIFY_CODE_VERIFIER from authorization_code_pkce_url.py")

    auth = AuthorizationCodeAuth(client_id, client_secret, redirect_uri, code_verifier=code_verifier)
    access_token = auth.exchange_callback_url(callback_url, expected_state=expected_state)

    print("access_token:", access_token)
    if auth.refresh_token is not None:
        print("refresh_token:", auth.refresh_token)


if __name__ == "__main__":
    main()
