from _bootstrap import bootstrap

bootstrap()

from spotapi import user_client


def main():
    client = user_client()
    user = client.me()

    print("id:", user.id)
    print("display_name:", user.display_name)
    print("product:", user.product)


if __name__ == "__main__":
    main()
