import os

from _local_oauth import example_scopes
from spotapi import AuthorizationCodeAuth, generate_code_verifier


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080")

    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")

    code_verifier = generate_code_verifier()
    auth = AuthorizationCodeAuth(
        client_id,
        client_secret,
        redirect_uri,
        scope=example_scopes(),
        code_verifier=code_verifier,
    )

    print("code_verifier:", code_verifier)
    print(auth.authorize_url(state="spotapi-pkce-example", show_dialog=True))


if __name__ == "__main__":
    main()
