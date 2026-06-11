from _bootstrap import bootstrap

bootstrap()

from spotapi import SpotifyClient, snapshot_id
from spotapi import config_value, load_config, require_write_examples


TRACK_URI = "spotify:track:11dFghVXANMlKmJXsNCbNl"


def main():
    require_write_examples()
    config = load_config()
    playlist_id = config_value(config, "playlist_id")
    if not playlist_id:
        raise SystemExit("Set playlist_id in spotapi.local.json")

    client = SpotifyClient()
    result = client.add_playlist_items(playlist_id, [TRACK_URI])

    print("snapshot_id:", snapshot_id(result))


if __name__ == "__main__":
    main()
