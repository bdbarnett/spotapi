from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()
    queue = client.queue()

    if queue.currently_playing is not None:
        print("currently_playing:", queue.currently_playing.name)
    else:
        print("currently_playing: None")

    if not queue.queue:
        print("queue: empty")
        return

    print("queue:")
    for item in queue.queue:
        print("-", item.type, item.name)


if __name__ == "__main__":
    main()
