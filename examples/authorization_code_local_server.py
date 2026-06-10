import os

from _local_oauth import REDIRECT_URI, open_authorize_url_and_wait, print_tokens, save_tokens
from _local_oauth import example_scopes
from spotapi import AuthorizationCodeAuth


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    state = os.environ.get("SPOTIFY_AUTH_STATE", "spotapi-local-server")

    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")

    auth = AuthorizationCodeAuth(
        client_id,
        client_secret,
        REDIRECT_URI,
        scope=example_scopes(),
    )
    url = auth.authorize_url(state=state, show_dialog=True)
    callback_url = open_authorize_url_and_wait(url, "Spotify authorization received. You can close this window.")

    access_token = auth.exchange_callback_url(callback_url, expected_state=state)
    print_tokens(auth, access_token)
    save_tokens(auth)


if __name__ == "__main__":
    main()
