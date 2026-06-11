from _bootstrap import bootstrap

bootstrap()

from spotapi import SpotifyClient
from config import config_value, load_write_examples_config, require_write_examples


def main():
    require_write_examples()
    config = load_write_examples_config()
    user_id = config_value(config, "user_id")
    if not user_id:
        raise SystemExit("Set user_id in examples/write_examples.json")

    name = config_value(config, "playlist_name", "spotapi example playlist")
    description = config_value(
        config,
        "playlist_description",
        "Created by spotapi example code",
    )

    client = SpotifyClient()
    playlist = client.create_playlist(user_id, name, public=False, description=description)

    print("playlist:", playlist.name)
    print("id:", playlist.id)


if __name__ == "__main__":
    main()
