import base64
import os

from _local_oauth import refresh_token_client


def main():
    if os.environ.get("SPOTIFY_RUN_WRITE_EXAMPLE") != "1":
        raise SystemExit("Set SPOTIFY_RUN_WRITE_EXAMPLE=1 to upload a playlist cover image")

    playlist_id = os.environ.get("SPOTIFY_PLAYLIST_ID")
    image_path = os.environ.get("SPOTIFY_PLAYLIST_COVER_JPEG")

    if not playlist_id:
        raise SystemExit("Set SPOTIFY_PLAYLIST_ID")
    if not image_path:
        raise SystemExit("Set SPOTIFY_PLAYLIST_COVER_JPEG")

    with open(image_path, "rb") as file:
        base64_jpeg = base64.b64encode(file.read()).decode("ascii")

    client = refresh_token_client()
    client.set_playlist_cover_image(playlist_id, base64_jpeg)

    print("uploaded:", image_path)


if __name__ == "__main__":
    main()
