from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client(auth_state="spotapi-local-server")
    user = client.me()

    print("id:", user.id)
    print("display_name:", user.display_name)


if __name__ == "__main__":
    main()
