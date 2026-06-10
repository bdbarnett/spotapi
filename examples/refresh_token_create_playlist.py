import os

from _local_oauth import refresh_token_client


def main():
    if os.environ.get("SPOTIFY_RUN_WRITE_EXAMPLE") != "1":
        raise SystemExit("Set SPOTIFY_RUN_WRITE_EXAMPLE=1 to create a playlist")

    user_id = os.environ.get("SPOTIFY_USER_ID")
    if not user_id:
        raise SystemExit("Set SPOTIFY_USER_ID")

    name = os.environ.get("SPOTIFY_PLAYLIST_NAME", "spotapi example playlist")
    description = os.environ.get("SPOTIFY_PLAYLIST_DESCRIPTION", "Created by spotapi example code")

    client = refresh_token_client()
    playlist = client.create_playlist(user_id, name, public=False, description=description)

    print("playlist:", playlist.name)
    print("id:", playlist.id)


if __name__ == "__main__":
    main()
