from _bootstrap import bootstrap

bootstrap()

from spotapi import SpotifyClient


def main():
    client = SpotifyClient(auth_state="spotapi-pkce-local-server")
    user = client.me()

    print("id:", user.id)
    print("display_name:", user.display_name)


if __name__ == "__main__":
    main()
