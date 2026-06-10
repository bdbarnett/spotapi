from _local_oauth import refresh_token_client


def main():
    client = refresh_token_client()
    user = client.me()

    print("id:", user.id)
    print("display_name:", user.display_name)
    print("product:", user.product)


if __name__ == "__main__":
    main()
