from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client
from spotapi.config import require_write_examples


TRACK_ID = "11dFghVXANMlKmJXsNCbNl"


def main():
    require_write_examples()
    client = user_client()
    client.save_tracks([TRACK_ID])

    saved = client.contains_saved_tracks([TRACK_ID])
    print("saved:", saved[0])


if __name__ == "__main__":
    main()
