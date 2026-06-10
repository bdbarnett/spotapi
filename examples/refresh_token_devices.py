from _local_oauth import refresh_token_client


def main():
    client = refresh_token_client()
    devices = client.devices()

    if not devices:
        print("No available devices.")
        return

    for device in devices:
        print("id:", device.id)
        print("name:", device.name)
        print("type:", device.type)
        print("active:", device.is_active)
        print("volume_percent:", device.volume_percent)
        print()


if __name__ == "__main__":
    main()
