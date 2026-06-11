from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client
from spotapi.config import config_value, load_config, require_write_examples


DEFAULT_TRACK_URI = "spotify:track:11dFghVXANMlKmJXsNCbNl"


def main():
    require_write_examples()
    config = load_config()
    uri = config_value(config, "track_uri", DEFAULT_TRACK_URI)

    client = user_client()
    client.add_to_queue(uri)

    print("queued:", uri)


if __name__ == "__main__":
    main()
