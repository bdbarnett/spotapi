from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()

    for device in client.devices():
        print("-", device.name, device.type, device.is_active)


if __name__ == "__main__":
    main()
